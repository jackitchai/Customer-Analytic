from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import *
from pyspark.sql.functions import *
from config import configuration

def main():
    spark = SparkSession.builder.appName("SmartCityStreaming")\
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.1,"
                "org.apache.hadoop:hadoop-aws:3.3.1,"
                "com.amazonaws:aws-java-sdk:1.11.469") \
        .config("spark.hadoop.fs.s3a.access.key", configuration.get("AWS_ACCESS_KEY_ID")) \
        .config("spark.hadoop.fs.s3a.secret.key", configuration.get("AWS_SECRET_ACCESS_KEY")) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config('spark.hadoop.f3.s3a.aws.credentials.provider','org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider') \
        .getOrCreate()



    spark.sparkContext.setLogLevel('WARN')
    
    # Print message indicating successful connection
    print("MinIO S3 connection successful.")    
    
    vehicleSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("location", StringType(), True),
        StructField("speed", DoubleType(), True),
        StructField("direction", StringType(), True),
        StructField("make", StringType(), True),
        StructField("model", StringType(), True),
        StructField("year", IntegerType(), True),
        StructField("fueltype", StringType(), True)
    ])
    
    gpsSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("speed", DoubleType(), True),
        StructField("direction", StringType(), True),
        StructField("vehicleType", StringType(), True),
    ])  
    
    trafficSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("location", DoubleType(), True),
        StructField("camera_id", StringType(), True),
        StructField("snapshot", StringType(), True),
    ])  
    
    weatherSchema = StructType([
        StructField("id", StringType(), True),
        StructField("deviceId", StringType(), True),
        StructField("location", StringType(), True),
        StructField("timestamp", TimestampType(), True),
        StructField("temperature",DoubleType(), True),
        StructField("weatherCondition", StringType(), True),
        StructField("precipitation", DoubleType(), True),
        StructField("humidity", DoubleType(), True),
        StructField("windSpeed", IntegerType(), True),
        StructField("airQualityIndex", DoubleType(), True)
    ])
    
    
    def read_kafka_topic(topic, schema):
        return (
            spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", 'broker:29092') \
            .option("subscribe", topic) \
            .option("startingOffsets", "earliest") \
            .load()
            .selectExpr('CAST(value AS STRING)')
            .select(from_json(col('value'), schema).alias('data'))
            .select('data.*')
            .withWatermark('timestamp', '2 minutes')
        )
        
    def streamWriter(input: DataFrame,checkpointFolder, output):
        return (
            input.writeStream
            .format('parquet')
            .option('checkpointLocation', checkpointFolder)
            .option('path',output)
            .outputMode('append')
            .start()
            
        )
    
    vehicleDF = read_kafka_topic('vehicle_data', vehicleSchema).alias('vehicle')
    gpsDF = read_kafka_topic('gps_data', gpsSchema).alias('gps')
    trafficDF = read_kafka_topic('traffic_camera_data', trafficSchema).alias('traffic')
    weatherDF = read_kafka_topic('weather_data', weatherSchema).alias('weather')
    
    # Print schema of each DataFrame
    print("Schema for Vehicle Data:")
    vehicleDF.printSchema()

    print("Schema for GPS Data:")
    gpsDF.printSchema()

    print("Schema for Traffic Camera Data:")
    trafficDF.printSchema()

    print("Schema for Weather Data:")
    weatherDF.printSchema()
        
    query1 = streamWriter(vehicleDF, 's3a://spark-streaming-data/checkpoints/vehicle-data', 's3a://spark-streaming-data/data/vehicle-data')
    query2 = streamWriter(gpsDF, 's3a://spark-streaming-data/checkpoints/gps-data', 's3a://spark-streaming-data/data/gps-data')
    query3 = streamWriter(trafficDF, 's3a://spark-streaming-data/checkpoints/traffic-data', 's3a://spark-streaming-data/data/traffic-data')
    query4 = streamWriter(weatherDF, 's3a://spark-streaming-data/checkpoints/weather-data', 's3a://spark-streaming-data/data/weather-data')

    query4.awaitTermination()


if __name__ == '__main__':
    main()