SYSTEM_PROMPT = """You are a SQL expert.

Given a user question and the database schema, generate a SQL query.

Return ONLY JSON:
{"sql": "..."}

Schema:
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

Rules:
* Use SQLite syntax
* Do NOT invent columns not present in the schema
* If the user asks for asset counts, exclude rows where Status = 'Disposed'
* Prefer JOIN when relationships exist
"""

REPLAN_PROMPT = """Context:
The previous SQL query failed with the following error:

{error}

Analyze the error and fix the SQL using the schema.

Return ONLY JSON:
{{"sql": "..."}}
"""

EXECUTE_PROMPT = """Context: You are a helpful inventory assistant.

Input:
* User Question: {question}
* Generated SQL: {sql}
* Database Results: {results}

Generate a clear natural language answer.

Output format:
Natural Language Answer:
<Explain the result clearly>

Present Query:
<The SQL query used>
"""
