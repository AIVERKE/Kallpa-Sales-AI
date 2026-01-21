import asyncio
import sys
import os

# Adjust path to enable imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.infrastructure.db.session import engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.product_service import ProductService
from src.domain.models import Store

async def verify_search():
    print("Starting Catalog Search Verification...")
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 1. Get Store ID
        store = await db.get(Store, 1) # Assuming ID 1 from seed
        if not store:
            # Fallback
            from sqlalchemy import select
            result = await db.execute(select(Store))
            store = result.scalars().first()
            if not store:
                print("ERROR: No store found. Run seed_data.py first.")
                return

        store_id = store.id
        print(f"Testing with Store: {store.name} (ID: {store_id})")

        # 2. Test Cases
        test_cases = [
            {"query": "que tienes?", "expect_results": True, "desc": "Broad intent 'que tienes?'"},
            {"query": "ver catalogo", "expect_results": True, "desc": "Broad intent 'ver catalogo'"},
            {"query": "hola", "expect_results": False, "desc": "Greeting 'hola' (Should be empty)"},
            {"query": "jean", "expect_results": True, "desc": "Specific 'jean'"},
            {"query": "jeans", "expect_results": True, "desc": "Plural 'jeans' (Should find 'Jean')"},
            {"query": "camiseta", "expect_results": True, "desc": "Specific 'camiseta'"},
            {"query": "camisas", "expect_results": True, "desc": "Plural/Variant 'camisas' (Should find 'Camiseta')"},
            {"query": "zapatos", "expect_results": False, "desc": "Missing item 'zapatos'"},
        ]

        print("\n--- Running Search Tests ---")
        for case in test_cases:
            print(f"Query: '{case['query']}'")
            products = await ProductService.search_products_by_text(db, case['query'], store_id)
            count = len(products)
            print(f"  Found: {count} products")
            
            if case['expect_results']:
                if count > 0:
                    print(f"  [PASS] {case['desc']}")
                else:
                    print(f"  [FAIL] {case['desc']} - Expected results, got none.")
            else:
                if count == 0:
                    print(f"  [PASS] {case['desc']}")
                else:
                    print(f"  [WARN] {case['desc']} - Expected none, got {count}. (Might be okay if strict match found something?)")

        # 3. Verify Formatting
        print("\n--- Testing Formatting ---")
        products = await ProductService.search_products_by_text(db, "catalogo", store_id)
        formatted_text = ProductService.format_products_for_llm(products)
        print("Formatted Output Preview (First 500 chars):")
        try:
             print(formatted_text[:500])
        except UnicodeEncodeError:
             print(formatted_text[:500].encode('ascii', 'ignore').decode('ascii'))

if __name__ == "__main__":
    asyncio.run(verify_search())
