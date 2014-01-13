# coding: utf-8
"""
Testing models behavior

"""
from tests import AppTestCase
#from models import Product


class TestProduct(AppTestCase):
    """
    Test Product model methods
    
    Init test connection from shell:
    >>> from app import app
    >>> from database import init_connection, select_db
    >>> app.config['TESTING'] = True
    >>> conn = init_connection(app)
    >>> db = select_db(app, conn)
    
    """
    
    def setUp(self):
        """
        Create few products in a tree
        
        Template
         |
         |-Product
            |
            |-Subproduct
        
        """
        
        products_collection = self.mongo_db.products
        
        template = products_collection.Product()
        template.name = u"Base product"
        template.description = u"Template for properties inheritance"
        template.price = 0.0
        template.is_template = True
        template.save()
        self.template = template
        
        product = products_collection.Product()
        product.name = u"Pizza"
        product.description = u"Common product"
        product.price = 10.0
        product.is_template = False
        product.parent = template._id
        product.save()
        self.product = product
        
        subproduct = products_collection.Product()
        subproduct.name = u"Pizza (supper)"
        subproduct.description = u"Common subproduct"
        subproduct.price = 15.0
        subproduct.is_template = False
        subproduct.parent = product._id
        subproduct.save()
        self.subproduct = subproduct
        
        # add property to template product
        template.add_property(u"is_flag", True, True)
    
    def tearDown(self):
        """Remove test products"""
        
        #self.mongo_db.products.drop()
    
    def test_add_property(self):
        """Check if property added to all descendants"""
        
        #products_collection = self.mongo_db.products
        
        # check property on common product
        #subproduct = products_collection.Product.find_one({"name": u"Pizza (supper)"})
        self.subproduct.reload()
        num = len(self.subproduct.properties)
        self.assertEqual(num, 1, "Wrong quantity of product properties: " + str(num))
        
    def test_del_property(self):
        """Check if property is deleted on descendants"""
        
        #products_collection = self.mongo_db.products
        
        #product = products_collection.Product.find_one({"name": u"Pizza"})
        product = self.product
        subproduct = self.subproduct
        
        product.reload()
        product.del_property("is_flag")
        
        # not recursively
        self.assertEqual(len(product.properties), 1, "Wrong quantity of product properties")
        self.assertEqual(product.properties[0]['is_deleted'], True, "Property isn't marked as deleted")
        
        # recursively
        product.del_property("is_flag", True)
        self.assertEqual(len(product.properties), 0, "Wrong quantity of properties on product")
        
        #subproduct = products_collection.Product.find_one({"name": u"Pizza (supper)"})
        subproduct.reload()
        self.assertEqual(len(subproduct.properties), 0, "Wrong quantity of properties on subproduct")
    
    
    
