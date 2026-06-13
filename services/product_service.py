"""
Product Service - Enhanced for Clothing Inventory
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from models.product import Product, ProductCategory, ProductUnit, StockSourceType


class ProductService:
    def __init__(self, session: Session):
        self.session = session

    # نقشه واحد بر اساس دسته‌بندی
    CATEGORY_UNIT_MAP = {
        ProductCategory.FABRIC: ProductUnit.METER,
        ProductCategory.PANTS: ProductUnit.PIECE,
        ProductCategory.JACKET: ProductUnit.PIECE,
    }

    def _generate_system_code(self) -> str:
        """تولید کد سیستمی PRD-XXXXXX"""
        last_product = (
            self.session.query(Product.code)
            .filter(Product.code.like("PRD-%"))
            .order_by(Product.code.desc())
            .first()
        )
        if not last_product:
            return "PRD-000001"
        try:
            last_num = int(last_product[0].split("-")[1])
            return f"PRD-{str(last_num + 1).zfill(6)}"
        except (IndexError, ValueError):
            count = self.session.query(Product).count()
            return f"PRD-{str(count + 1).zfill(6)}"

    def _generate_numeric_code(self) -> str:
        """تولید کد عددی منحصر به فرد 8 رقمی"""
        last_product = (
            self.session.query(Product.numeric_code)
            .order_by(Product.numeric_code.desc())
            .first()
        )
        if not last_product:
            return "10000001"
        try:
            last_num = int(last_product[0])
            return str(last_num + 1)
        except ValueError:
            # اگر خطایی بود، از تعداد محصولات استفاده کن
            count = self.session.query(Product).count()
            return str(10000001 + count)

    def _get_unit_for_category(self, category: ProductCategory) -> ProductUnit:
        """واحد را بر اساس دسته‌بندی برمی‌گرداند"""
        return self.CATEGORY_UNIT_MAP.get(category, ProductUnit.PIECE)

    def create_product(
        self,
        name: str,
        category: ProductCategory,
        initial_stock: float = 0,
        default_price: float = 0,
        stock_source: StockSourceType = StockSourceType.PURCHASE
    ) -> Product:
        """ایجاد محصول جدید با تمام فیلدهای جدید"""

        # تولید کدها
        system_code = self._generate_system_code()
        numeric_code = self._generate_numeric_code()

        # تعیین واحد بر اساس دسته‌بندی
        unit = self._get_unit_for_category(category)

        product = Product(
            code=system_code,
            numeric_code=numeric_code,
            name=name,
            category=category,
            unit=unit,
            initial_stock=max(0, initial_stock),
            stock_quantity=max(0, initial_stock),
            default_price=max(0, default_price),
            stock_source=stock_source
        )

        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def get_product_by_id(self, product_id: int) -> Product | None:
        return self.session.query(Product).filter(Product.id == product_id).first()

    def get_product_by_numeric_code(self, numeric_code: str) -> Product | None:
        """جستجو با کد عددی"""
        return self.session.query(Product).filter(Product.numeric_code == numeric_code).first()

    def get_product_by_code(self, code: str) -> Product | None:
        """جستجو با کد سیستمی"""
        return self.session.query(Product).filter(Product.code == code).first()

    def search_products(self, query: str = None, category: ProductCategory = None):
        db_query = self.session.query(Product)
        if query:
            db_query = db_query.filter(
                or_(
                    Product.name.contains(query),
                    Product.code.contains(query),
                    Product.numeric_code.contains(query)
                )
            )
        if category:
            db_query = db_query.filter(Product.category == category)
        return db_query.all()

    def get_all_products(self):
        return self.session.query(Product).order_by(Product.numeric_code.desc()).all()

    def update_product(self, product_id: int, **kwargs) -> Product:
        """به‌روزرسانی محصول"""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"محصول با شناسه {product_id} یافت نشد")

        PROTECTED_FIELDS = {"id", "code", "numeric_code", "unit"}

        for key, value in kwargs.items():
            if key in PROTECTED_FIELDS:
                continue
            if hasattr(product, key):
                if key in ["stock_quantity", "initial_stock", "default_price"]:
                    value = max(0, float(value))
                setattr(product, key, value)

        self.session.commit()
        self.session.refresh(product)
        return product

    def delete_product(self, product_id: int):
        product = self.get_product_by_id(product_id)
        if product:
            self.session.delete(product)
            self.session.commit()

    def get_current_stock(self, product_id: int) -> float:
        """دریافت موجودی فعلی"""
        product = self.get_product_by_id(product_id)
        return product.stock_quantity if product else 0

    def adjust_stock(self, product_id: int, quantity_change: float) -> float:
        """تغییر موجودی"""
        product = self.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"محصول با شناسه {product_id} یافت نشد")

        new_stock = product.stock_quantity + quantity_change
        if new_stock < 0:
            raise ValueError(
                f"موجودی کافی نیست. فعلی: {product.stock_quantity} {product.unit.value}, "
                f"تغییر: {quantity_change} {product.unit.value}"
            )

        product.stock_quantity = new_stock
        self.session.commit()
        self.session.refresh(product)
        return new_stock