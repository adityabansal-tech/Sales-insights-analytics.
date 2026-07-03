"""
Basic tests for the ETL pipeline. Run with: python -m pytest tests/
(or python -m unittest tests.test_pipeline if pytest isn't installed)
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sales_engine import transform
import pandas as pd


class TestTransform(unittest.TestCase):

    def test_clean_fact_sales_drops_duplicates(self):
        df = pd.DataFrame({
            "line_id": [1, 1, 2],
            "order_date": ["2024-01-01", "2024-01-01", "2024-01-02"],
            "customer_id": [1, 1, 2],
            "product_id": [1, 1, 2],
            "quantity": [2, 2, 3],
            "unit_price": [10.0, 10.0, 20.0],
            "discount": [0.0, 0.0, 0.1],
        })
        cleaned = transform.clean_fact_sales(df)
        self.assertEqual(len(cleaned), 2)

    def test_clean_fact_sales_drops_invalid_quantity(self):
        df = pd.DataFrame({
            "line_id": [1, 2],
            "order_date": ["2024-01-01", "2024-01-02"],
            "customer_id": [1, 2],
            "product_id": [1, 2],
            "quantity": [0, 3],
            "unit_price": [10.0, 20.0],
            "discount": [0.0, 0.1],
        })
        cleaned = transform.clean_fact_sales(df)
        self.assertEqual(len(cleaned), 1)

    def test_clean_fact_sales_recomputes_sales_amount(self):
        df = pd.DataFrame({
            "line_id": [1],
            "order_date": ["2024-01-01"],
            "customer_id": [1],
            "product_id": [1],
            "quantity": [2],
            "unit_price": [100.0],
            "discount": [0.1],
        })
        cleaned = transform.clean_fact_sales(df)
        self.assertAlmostEqual(cleaned.iloc[0]["sales_amount"], 180.0)

    def test_clean_dimension_drops_null_keys(self):
        df = pd.DataFrame({"product_id": [1, None, 3], "name": ["a", "b", "c"]})
        cleaned = transform.clean_dimension(df, "product_id")
        self.assertEqual(len(cleaned), 2)


if __name__ == "__main__":
    unittest.main()
