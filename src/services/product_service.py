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
        import re
        # Remove punctuation (keep alphanumeric and spaces)
        clean_query = re.sub(r'[^\w\s]', '', query_text.strip().lower())
        
        # Keywords that imply "Show me everything" or "What do you have?"
        BROAD_MATCH_KEYWORDS = {
            "catalogo", "catálogo", "lista", "productos", "vendes", 
            "tienes", "stock", "precio", "precios", "comprar", 
            "disponible", "ver", "mostrame", "muéstrame", "muestrame",
            "quiero", "busco", "necesito", "quisiera"
        }
        
        words = clean_query.split()
        
        # Check if broad match
        is_broad_intent = any(w in BROAD_MATCH_KEYWORDS for w in words)
            
        # Filter search terms: Words > 3 chars AND NOT in BROAD_MATCH_KEYWORDS
        search_terms = [w for w in words if len(w) > 3 and w not in BROAD_MATCH_KEYWORDS] 

        # If it's a broad intent or we have valid search terms
        if not search_terms and not is_broad_intent:
            return []

        # Build Query
        statement = select(Product).options(selectinload(Product.variants)).where(Product.store_id == store_id).where(Product.status == "active")

        if not search_terms:
            # Return top 10 active products if purely broad intent (e.g. "que tienes?")
            # or if keywords stripped all terms resulting in empty search list but valid intent
            statement = statement.limit(10)
        else:
             # Specific Search
            conditions = []
            for term in search_terms:
                # Basic Plural Handling: Try to match singular forms too
                variations = {term}
                if term.endswith('s'):
                    variations.add(term[:-1]) # jeans -> jean
                if term.endswith('es'):
                    variations.add(term[:-2]) # colores -> color
                
                # Special Cases (Manual Stemming/Synonyms)
                if term == "camisas": contents = variations.add("camiseta")
                if term == "poleras": variations.add("camiseta")
                if term == "pols": variations.add("polo") # Typo handling example
                
                # Create OR group for this term's variations
                term_conditions = []
                for var in variations:
                    term_conditions.append(col(Product.name).ilike(f"%{var}%"))
                    term_conditions.append(col(Product.description).ilike(f"%{var}%"))
                    term_conditions.append(col(Product.category).ilike(f"%{var}%"))
                    # Variant fields
                    term_conditions.append(col(ProductVariant.color).ilike(f"%{var}%"))
                    term_conditions.append(col(ProductVariant.sku).ilike(f"%{var}%"))
                
                # Combine variations with OR, and add to main AND list? 
                # Wait, strictly we want (TermA_Var1 OR TermA_Var2) AND (TermB_Var1 OR TermB_Var2) 
                # But current logic was `conditions.append...` which implies OR across ALL terms if we use `or_(*conditions)`.
                # Original logic: `where(or_(*conditions))` -> Any term matching any field is enough.
                # So we just dump all variations into the big OR list.
                conditions.extend(term_conditions)
            
            statement = statement.outerjoin(ProductVariant).where(or_(*conditions))

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
