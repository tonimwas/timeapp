from django.db import connection

cursor = connection.cursor()
cursor.execute('DROP TABLE IF EXISTS "trips_place" CASCADE;')
cursor.execute("""
CREATE TABLE "trips_place" (
    "slug" varchar(50) NOT NULL PRIMARY KEY,
    "name" varchar(200) NOT NULL,
    "category" varchar(50) NOT NULL,
    "neighbourhood" varchar(100) NOT NULL,
    "lat" double precision NOT NULL,
    "lng" double precision NOT NULL,
    "entry_fee" integer NOT NULL CHECK ("entry_fee" >= 0),
    "avg_food" integer NOT NULL CHECK ("avg_food" >= 0),
    "duration_min" integer NOT NULL CHECK ("duration_min" >= 0),
    "rating" numeric(3, 1) NOT NULL,
    "price_tier" varchar(20) NOT NULL,
    "tags" jsonb NOT NULL,
    "vibes" jsonb NOT NULL,
    "popularity" numeric(3, 2) NOT NULL
);
""")
cursor.execute("""
CREATE INDEX "trips_place_slug_90fae0fe_like" ON "trips_place" ("slug" varchar_pattern_ops);
""")
cursor.close()
