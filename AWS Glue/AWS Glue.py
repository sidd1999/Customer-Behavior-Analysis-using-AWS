import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import col, avg, sum

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Load data from Glue Catalog
processed_data = glueContext.create_dynamic_frame.from_catalog(
    database="your_database_name",  # Replace with your database name
    table_name="your_table_name"    # Replace with your table name
)

# Convert DynamicFrame to DataFrame for easier data manipulation
df = processed_data.toDF()

# Data Cleansing: Remove duplicates
df = df.dropDuplicates()

# Data Cleansing: Filter out rows where 'product_id' or 'views' are missing
df = df.filter(df['product_id'].isNotNull() & df['views'].isNotNull())

# Data Cleansing: Fill missing values in 'sales' with 0
df = df.fillna({'sales': 0})

# Data Aggregation: Group by 'product_id' and aggregate metrics
aggregated_df = df.groupBy("product_id").agg(
    sum("sales").alias("total_sales"),
    avg("views").alias("average_views")
)

# Data Format Conversion: Convert back to DynamicFrame for writing to S3
aggregated_dyf = DynamicFrame.fromDF(aggregated_df, glueContext, "aggregated_dyf")

# Write the transformed data back to S3 in Parquet format
glueContext.write_dynamic_frame.from_options(
    frame=aggregated_dyf,
    connection_type="s3",
    connection_options={"path": "s3://clickstream-data-sidd99/processed_output/"},
    format="parquet"
)

# Commit job
job.commit()