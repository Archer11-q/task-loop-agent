import os


# storage层开关，json存储 || SQLite存储
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND","json")