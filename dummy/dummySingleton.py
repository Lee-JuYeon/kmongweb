from utils.kmong_checker import dbLib
from datetime import datetime  # datetime 모듈 import 추가
import json

class DummySingleton:
    _instance = None  # 싱글톤 인스턴스 저장용

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data = cls._generate_dummy_data()
            cls._instance.testAdminInfo = cls._generate_admin_info()
        return cls._instance

    @staticmethod
    def _generate_admin_info():
        return {
            "email": "cavss1118@gmail.com",
            "password": "vlwk!!12",
            "login_cookie": json.dumps({"KMONG_BOOKMARK_GIGS": "eyJpdiI6Imc3Zmg0QTZCUUFvQUVNeDd1L2xVRWc9PSIsInZhbHVlIjoiMWsvaUkrM2Y2eVZhUGgwWnRYQndwOGxwWE1wR1Ivd21aRzkxN0IzaVp5ZGxGRmJNTCtsUmNPZEc0Y1UybW5UZCIsIm1hYyI6IjNkNzEwNjU0YmFjOWU1MDAzZjcwMmU4MDJjMTY1N2I1ZWVlOTRlYjU3NjM0MDNiYTNhYzRlZDhjNWQxOGFiOTciLCJ0YWciOiIifQ%3D%3D", "kmong_session": "eyJpdiI6Inp3ZFRhNm1wTGcrcS9TTGJBclBYcWc9PSIsInZhbHVlIjoiblNrdVZaTEo3cCtTaXByZHRXaElyZ2VWbHpjUXIxbmxPdUhQUlhyU1RONlZJSUQyQk9rYUdjcWJiMFFEOHVDYW1oMXlJV1p5dDdMQVA5ZkhhUVYyNmhXRnc0TFQxVldnMUZPQTBvd2Y3c1lZWkp6S0FyZ1ExUitVaERQaTdXUVUiLCJtYWMiOiJjOGQ2MWE2NDViYjZhMjk5MDBjZjU5ZmVkNWE1NGM4ZjE0MWQ4YTk4Y2Q1OWZkZjc1MDZmNTk3NmZhMmJjNTUwIiwidGFnIjoiIn0%3D", "remember_kmong_web_59ba36addc2b2f9401580f014c7f58ea4e30989d": "eyJpdiI6ImFNUlZNamFpYVdJNEV1VUxpZUNDNEE9PSIsInZhbHVlIjoiS0JzWll1bFRyeU8yS0tEZEh1NTVRSmgvVmhXOUlrV21mdVByWWFqUVA0OERoeFJSdVd2VFZ4UVpvNUgzQmhqWU9ZTVQ2L3Y0VkVjNks5ZTI5V1RJRUVOU2Jyb01XUW03SGt6YjgvQldzeWhrWk1vME9XUDRTaE45cVd3bDB1L2w0RmRhUWdUVHJtQS9SbG5JWWI1bTRGN0lTNExPZFdpbTYxL0xJc0tETWo4TmR2OEUwQXhKc1hWWk55QzVMcGV0Q0dza25NTGw0V1JZZUdCK3BWWGJ2NFZSTUlXL3o0dU56aU5SL2I3elZxL2N3aHFmNXl4RFQ0Mk9wYm9MTHpZdSIsIm1hYyI6ImMzZDI0MTdkMDg0Nzk0NTRkYWMwNzgwYjE2ZjZiZTMxMWM5N2VkMDUxMzYyZmJmYTEyMjMwYzIyY2FkYzYwYzUiLCJ0YWciOiIifQ%3D%3D"})
        }

    def get_admin_info(self):  # self 추가
        return self.testAdminInfo

    @staticmethod
    def _generate_client_info():
        return {
            "email": "",
            "password": "",
            "login_cookie": {}
        }

    @staticmethod
    def _generate_dummy_data():
        return [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
        ]

    def get_data(self):
        return self.data

    def add_data(self, new_item):
        self.data.append(new_item)

    def remove_data(self, item_id):
        self.data = [item for item in self.data if item["id"] != item_id]
