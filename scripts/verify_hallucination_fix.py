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

async def verify_fix():
    print("Starting Hallucination Fix Verification...")
    
    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 1. Get Store ID
        store = await db.get(Store, 1) # Assuming ID 1 from seed
        if not store:
            # Fallback if ID 1 doesn't exist, try to find any store
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
            {
                "desc": "Exact Match: Jean Azul 38",
                "name": "Jean Clásico Stonewash",
                "color": "Azul Clásico",
                "size": "38",
                "expected_sku": "JEAN-AZ-38"
            },
            {
                "desc": "Case Insensitive: jean azul 38",
                "name": "jean clásico stonewash",
                "color": "azul clásico",
                "size": "38",
                "expected_sku": "JEAN-AZ-38"
            },
            {
                "desc": "Partial/Fuzzy Color: Azul (instead of Azul Clásico)",
                "name": "Jean Clásico Stonewash",
                "color": "Azul", # Simulating LLM being brief
                "size": "38",
                "expected_sku": "JEAN-AZ-38" 
            },
             {
                "desc": "T-Shirt Match: White M",
                "name": "Camiseta Oversize Kallpa",
                "color": "Blanco",
                "size": "M",
                "expected_sku": "TSHIRT-BL-M"
            }
        ]

        print("\n--- Running Logic Tests ---")
        for case in test_cases:
            print(f"Testing: {case['desc']}")
            variant = await ProductService.find_best_match_variant(
                db, 
                store_id, 
                case['name'], 
                case['color'], 
                case['size']
            )
            
            if variant:
                print(f"  Result: Found SKU {variant.sku}")
                if variant.sku == case['expected_sku']:
                    print("  [PASS]")
                else:
                    print(f"  [FAIL] Expected {case['expected_sku']}, got {variant.sku}")
            else:
                # For "Azul" fuzzy match, it might fail if logic isn't fuzzy enough. This is what we want to test.
                print("  [WARN] Result: No variant found.")

        # 3. Simulate "Hallucinated SKU" scenario
        # Imagine LLM sends SKU: "JEAN-FAKE-99" but correct attributes
        print("\n--- Simulating Hallucination Scenario ---")
        hallucinated_sku = "JEAN-FAKE-99"
        real_sku = "JEAN-AZ-38"
        print(f"Scenario: LLM sends SKU '{hallucinated_sku}' but attributes for '{real_sku}'")
        
        # logic in chat_service uses the attributes to override if present
        # We just test that find_best_match_variant returns the object regardless of what SKU we 'thought' we had.
        variant = await ProductService.find_best_match_variant(
            db,
            store_id,
            "Jean Clásico Stonewash",
            "Azul Clásico",
            "38"
        )
        
        if variant and variant.sku == real_sku:
             print("  [PASS] Logic correctly identified the real product from attributes.")
        else:
             print("  [FAIL] Could not recover from attributes.")

if __name__ == "__main__":
    asyncio.run(verify_fix())
