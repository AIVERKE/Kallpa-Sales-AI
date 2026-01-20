from typing import List
from sqlalchemy import or_
from sqlmodel import select, col
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import Product, ProductVariant

class ProductService:
    @staticmethod
    async def search_products_by_text(db: AsyncSession, query_text: str, store_id: int) -> List[Product]:
        """
        Searches products by name or description using a simple case-insensitive partial match.
        Includes variants in the result.
        """
        # Clean query text
        clean_query = query_text.strip().lower()
        
        # Strategy:
        # 1. Split message into words.
        # 2. Filter out short words (stop words approximation).
        # 3. Search for ANY word matching product name/desc/category.
        
        words = clean_query.split()
        search_terms = [w for w in words if len(w) > 3] # Ignora "un", "de", "el", etc.

        if not search_terms:
            return []

        # Build dynamic OR clauses for each term
        # We search in Product fields AND Variant fields
        conditions = []
        for term in search_terms:
            conditions.append(col(Product.name).ilike(f"%{term}%"))
            conditions.append(col(Product.description).ilike(f"%{term}%"))
            conditions.append(col(Product.category).ilike(f"%{term}%"))
            # Variant fields
            conditions.append(col(ProductVariant.color).ilike(f"%{term}%"))
            conditions.append(col(ProductVariant.size).ilike(f"%{term}%"))
            conditions.append(col(ProductVariant.sku).ilike(f"%{term}%"))

        statement = (
            select(Product)
            .outerjoin(ProductVariant) # JOIN to search in variants
            .where(Product.store_id == store_id)
            .where(Product.status == "active")
            .where(or_(*conditions))
            .options(selectinload(Product.variants))
        )
        
        result = await db.execute(statement)
        products = result.scalars().all()
        
        # Deduplicate results based on Product ID
        unique_products = {p.id: p for p in products}.values()
        return list(unique_products)

    @staticmethod
    def format_products_for_llm(products: List[Product]) -> str:
        """
        Converts a list of products and their variants into a string specifically formatted 
        for the LLM to understand availability.
        """
        if not products:
            return "No se encontraron productos específicos relacionados con la consulta en el inventario."

        lines = []
        for p in products:
            # Format variants
            variants_info = []
            # We need to access p.variants. CAUTION: in async this might fail if not loaded.
            # We'll assume for this step that we can access it or we'll fix the query above.
            # To be safe, let's catch standard errors or assume we need to fix the query in the next step if this fails.
            
            # Simple check if variants list is populated (if eager loaded)
            try:
                # Iterate variants
                for v in p.variants:
                    stock_msg = f"{v.stock_quantity} unidaes" if v.stock_quantity > 0 else "AGOTADO"
                    var_str = f"  - [CÓDIGO: {v.sku}] | Talla: {v.size or 'Única'} | Color: {v.color or 'Único'} | Precio: {v.additional_price + p.base_price} Bs. | Stock: {stock_msg}"
                    variants_info.append(var_str)
            except Exception:
                # If lazy load fails, we note it.
                variants_info.append("  - (Error cargando variantes: verificar carga ansiosa)")

            lines.append(f"Producto: {p.name}")
            lines.append(f"Descripción: {p.description or ''}")
            lines.append(f"Precio Base: {p.base_price} Bs.")
            if variants_info:
                lines.append("Variantes Disponibles:")
                lines.extend(variants_info)
            else:
                lines.append("Variantes: No especificadas (Consultar stock general)")
            lines.append("-" * 20)

        return "\n".join(lines)

    @staticmethod
    async def find_best_match_variant(
        db: AsyncSession, 
        store_id: int, 
        product_name_query: str, 
        color_query: str = None, 
        size_query: str = None
    ) -> ProductVariant:
        """
        Tries to find a single variant that matches the robust description.
        Useful when LLM hallucinates SKU but gets attributes right.
        """
        # 1. Find Product first (relaxed search)
        clean_name = product_name_query.strip().lower()
        product_result = await db.execute(
            select(Product)
            .where(Product.store_id == store_id)
            .where(
                or_(
                    col(Product.name).ilike(f"%{clean_name}%"),
                    col(Product.description).ilike(f"%{clean_name}%")
                )
            )
            .limit(1)
        )
        product = product_result.scalars().first()
        
        if not product:
            return None
            
        # 2. Find Variant by Attributes
        statement = select(ProductVariant).where(ProductVariant.product_id == product.id)
        
        if size_query and size_query.lower() != "única":
             statement = statement.where(col(ProductVariant.size).ilike(f"%{size_query}%"))
             
        if color_query and color_query.lower() != "único":
             statement = statement.where(col(ProductVariant.color).ilike(f"%{color_query}%"))
             
        # Order by stock availability preferentially
        statement = statement.order_by(ProductVariant.stock_quantity.desc())
        
        variant_result = await db.execute(statement)
        variant = variant_result.scalars().first()
        
        return variant
