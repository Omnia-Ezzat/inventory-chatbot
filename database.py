import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # Recreate for clean start

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # DDL
    schemas = [
        """
        CREATE TABLE IF NOT EXISTS ChatHistory (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            SessionId TEXT NOT NULL,
            Role TEXT NOT NULL,
            Content TEXT NOT NULL,
            Timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE Customers (
            CustomerId INTEGER PRIMARY KEY AUTOINCREMENT,
            CustomerCode TEXT UNIQUE NOT NULL,
            CustomerName TEXT NOT NULL,
            Email TEXT,
            Phone TEXT,
            BillingAddress1 TEXT,
            BillingCity TEXT,
            BillingCountry TEXT,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            IsActive INTEGER DEFAULT 1
        );
        """,
        """
        CREATE TABLE Vendors (
            VendorId INTEGER PRIMARY KEY AUTOINCREMENT,
            VendorCode TEXT UNIQUE NOT NULL,
            VendorName TEXT NOT NULL,
            Email TEXT,
            Phone TEXT,
            AddressLine1 TEXT,
            City TEXT,
            Country TEXT,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            IsActive INTEGER DEFAULT 1
        );
        """,
        """
        CREATE TABLE Sites (
            SiteId INTEGER PRIMARY KEY AUTOINCREMENT,
            SiteCode TEXT UNIQUE NOT NULL,
            SiteName TEXT NOT NULL,
            AddressLine1 TEXT,
            City TEXT,
            Country TEXT,
            TimeZone TEXT,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            IsActive INTEGER DEFAULT 1
        );
        """,
        """
        CREATE TABLE Locations (
            LocationId INTEGER PRIMARY KEY AUTOINCREMENT,
            SiteId INTEGER NOT NULL,
            LocationCode TEXT NOT NULL,
            LocationName TEXT NOT NULL,
            ParentLocationId INTEGER,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            IsActive INTEGER DEFAULT 1,
            UNIQUE(SiteId, LocationCode),
            FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
            FOREIGN KEY (ParentLocationId) REFERENCES Locations(LocationId)
        );
        """,
        """
        CREATE TABLE Items (
            ItemId INTEGER PRIMARY KEY AUTOINCREMENT,
            ItemCode TEXT UNIQUE NOT NULL,
            ItemName TEXT NOT NULL,
            Category TEXT,
            UnitOfMeasure TEXT,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            IsActive INTEGER DEFAULT 1
        );
        """,
        """
        CREATE TABLE Assets (
            AssetId INTEGER PRIMARY KEY AUTOINCREMENT,
            AssetTag TEXT UNIQUE NOT NULL,
            AssetName TEXT NOT NULL,
            SiteId INTEGER NOT NULL,
            LocationId INTEGER,
            SerialNumber TEXT,
            Category TEXT,
            Status TEXT DEFAULT 'Active',
            Cost REAL,
            PurchaseDate TEXT,
            VendorId INTEGER,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
            FOREIGN KEY (LocationId) REFERENCES Locations(LocationId),
            FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
        );
        """,
        """
        CREATE TABLE Bills (
            BillId INTEGER PRIMARY KEY AUTOINCREMENT,
            VendorId INTEGER NOT NULL,
            BillNumber TEXT NOT NULL,
            BillDate TEXT NOT NULL,
            DueDate TEXT,
            TotalAmount REAL NOT NULL,
            Currency TEXT DEFAULT 'USD',
            Status TEXT DEFAULT 'Open',
            CreatedAt TEXT,
            UpdatedAt TEXT,
            UNIQUE(VendorId, BillNumber),
            FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
        );
        """,
        """
        CREATE TABLE PurchaseOrders (
            POId INTEGER PRIMARY KEY AUTOINCREMENT,
            PONumber TEXT UNIQUE NOT NULL,
            VendorId INTEGER NOT NULL,
            PODate TEXT NOT NULL,
            Status TEXT DEFAULT 'Open',
            SiteId INTEGER,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId),
            FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
        );
        """,
        """
        CREATE TABLE PurchaseOrderLines (
            POLineId INTEGER PRIMARY KEY AUTOINCREMENT,
            POId INTEGER NOT NULL,
            LineNumber INTEGER NOT NULL,
            ItemId INTEGER,
            ItemCode TEXT NOT NULL,
            Description TEXT,
            Quantity REAL NOT NULL,
            UnitPrice REAL NOT NULL,
            UNIQUE(POId, LineNumber),
            FOREIGN KEY (POId) REFERENCES PurchaseOrders(POId),
            FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
        );
        """,
        """
        CREATE TABLE SalesOrders (
            SOId INTEGER PRIMARY KEY AUTOINCREMENT,
            SONumber TEXT UNIQUE NOT NULL,
            CustomerId INTEGER NOT NULL,
            SODate TEXT NOT NULL,
            Status TEXT DEFAULT 'Open',
            SiteId INTEGER,
            CreatedAt TEXT,
            UpdatedAt TEXT,
            FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId),
            FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
        );
        """,
        """
        CREATE TABLE SalesOrderLines (
            SOLineId INTEGER PRIMARY KEY AUTOINCREMENT,
            SOId INTEGER NOT NULL,
            LineNumber INTEGER NOT NULL,
            ItemId INTEGER,
            ItemCode TEXT NOT NULL,
            Description TEXT,
            Quantity REAL NOT NULL,
            UnitPrice REAL NOT NULL,
            UNIQUE(SOId, LineNumber),
            FOREIGN KEY (SOId) REFERENCES SalesOrders(SOId),
            FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
        );
        """,
        """
        CREATE TABLE AssetTransactions (
            AssetTxnId INTEGER PRIMARY KEY AUTOINCREMENT,
            AssetId INTEGER NOT NULL,
            FromLocationId INTEGER,
            ToLocationId INTEGER,
            TxnType TEXT NOT NULL,
            Quantity INTEGER DEFAULT 1,
            TxnDate TEXT,
            Note TEXT,
            FOREIGN KEY (AssetId) REFERENCES Assets(AssetId),
            FOREIGN KEY (FromLocationId) REFERENCES Locations(LocationId),
            FOREIGN KEY (ToLocationId) REFERENCES Locations(LocationId)
        );
        """
    ]

    for schema in schemas:
        cursor.execute(schema)

    # Seed Data
    cursor.executescript("""
    INSERT INTO Customers (CustomerCode, CustomerName, Email, BillingCity) VALUES 
        ('CUST001', 'Acme Corp', 'contact@acme.com', 'New York'),
        ('CUST002', 'Globex', 'info@globex.com', 'Springfield');
        
    INSERT INTO Vendors (VendorCode, VendorName, City) VALUES 
        ('VEND001', 'TechSupply Inc', 'San Francisco'),
        ('VEND002', 'OfficeWorld', 'Chicago');
        
    INSERT INTO Sites (SiteCode, SiteName, City) VALUES 
        ('HQ', 'Headquarters', 'New York'),
        ('WH1', 'Warehouse 1', 'New Jersey');
        
    INSERT INTO Locations (SiteId, LocationCode, LocationName) VALUES 
        (1, 'FL1', 'Floor 1'),
        (2, 'A1', 'Aisle 1');
        
    INSERT INTO Items (ItemCode, ItemName, Category) VALUES 
        ('ITM001', 'Laptop Pro', 'Electronics'),
        ('ITM002', 'Office Chair', 'Furniture');
        
    INSERT INTO Assets (AssetTag, AssetName, SiteId, LocationId, Status) VALUES 
        ('AST100', 'Laptop Pro - John', 1, 1, 'Active'),
        ('AST101', 'Meeting Table', 1, 1, 'Active'),
        ('AST102', 'Broken Chair', 1, 1, 'Disposed');
        
    INSERT INTO Bills (VendorId, BillNumber, BillDate, TotalAmount) VALUES 
        (1, 'B-1001', '2023-01-10', 5000.00),
        (2, 'B-1002', '2023-01-15', 250.00);

    INSERT INTO PurchaseOrders (PONumber, VendorId, PODate) VALUES 
        ('PO-2001', 1, '2023-01-05'),
        ('PO-2002', 2, '2023-01-10');
        
    INSERT INTO PurchaseOrderLines (POId, LineNumber, ItemId, ItemCode, Quantity, UnitPrice) VALUES 
        (1, 1, 1, 'ITM001', 5, 1000.00),
        (2, 1, 2, 'ITM002', 10, 25.00);
        
    INSERT INTO SalesOrders (SONumber, CustomerId, SODate) VALUES 
        ('SO-3001', 1, '2023-02-01'),
        ('SO-3002', 2, '2023-02-05');
        
    INSERT INTO SalesOrderLines (SOId, LineNumber, ItemId, ItemCode, Quantity, UnitPrice) VALUES 
        (1, 1, 1, 'ITM001', 2, 1200.00),
        (2, 1, 2, 'ITM002', 5, 30.00);
        
    INSERT INTO AssetTransactions (AssetId, TxnType, TxnDate) VALUES 
        (1, 'CheckIn', '2023-01-10'),
        (2, 'CheckOut', '2023-01-12');
    """)

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()
