# Korean Cosmetic Data Pipeline

![image](https://user-images.githubusercontent.com/53164959/211179000-201fd640-376e-4c3a-8644-7cd615011e9b.png)


# Architecture 
![image](https://user-images.githubusercontent.com/53164959/211186084-00b58740-86e9-4813-9226-03a2025d99ef.png)
<p align='center'>Fig 1. General Architecture</p>



Pipeline consits of various modules:

- Java Spring Framework (REST API is running on Google App Engine) 
- ETL jobs
- BigQuery Warehouse Module
- Analytics Module (Pandas and BigQuery)
- Visualization (Tableau)





# Overview

Data is captured in real-time from the rest-API using the Spring framework running on the google app engine. The data collected from API is stored on MongoDB and has undergone the first data transformation before moving to google storage. The first dag is triggered every week. 

# ETL Flow

 - Incoming data is scheduled to store in MongoDB. 
 
 - The first transformation is triggered which reads the data from the database and applies transformation. The dataset is repartitioned and moved to the processed
    zone.
    
 - The big query operator picks up data from the processed zone and applies the second transformation, which generates the metrics for marketing. 
 
 - The key metrics are stored in the External Database (i.e., MySQL) for later use. After the transfer finishes, the dag execution is complete. 
 
 - The visualization stage begins once the connection of the bing query to tableau is successful. 

# Cost (Why BigQuery?)

The cost of storage is the most vital aspect in deciding the final stage of storing data. I believe that the pricing model is straightforward and affordable on a small or large scale. The total dataset for this project is smaller than 500G in size, which is reasonably large for a structured. I was billed only slightly more than $5 per month for storage costs. In terms of query cost, you will not be spending much fortune since BigQuery is a columnar database which means the engine will only can your selected columns, which depends on the way you structure your data warehouse. 

With a reasonably sized structured data warehouse, you are looking for less than $150 per month, compared to the cheapest always on RedShift instance $245 per month. To me, the on-demand pricing of BigQuery is more desirable. 

# All the codes are the minimal version of actual project

There are some changes to the one I did at the production level.

First, in practice, I have used cloud composers as one of the fully managed workflow orchestration services for orchestra work. But the airflow is run on the local machine with a help of docker-compose. Therefore, you need to specify environment variables and prepare a docker image with the required python packages installed for your self. (If you are unfamilar to the last sentence, please follow the instructions below). 

Second, in practice, our team used Fast API as the backend. But I recently started to learn java codes and want to write some java codes for the project. That is why the spring framework is employed here ( There seem to be many improvements I need to make on the learning journey.)

Third, I  intentionally drop any codes that contain confidential information about the company I worked for. 

# Environment Setup

### 1. Setting Up Airflow

In order to install or update your packages for airflow, you first create either a new or updated image through DOCKERFILE. After save a requirements.txt (i.e., a file that saves a list of modules and packages required by your project), run the following code.

```sh
docker build . --tag {your_own_tag_name}

```
Once you have built the new image, copy the name for the newly created image. And paste the name to the section of image under &airflow-common in docker-compose file.

```sh
version: '3'
x-airflow-common:
  &airflow-common
  image: ${AIRFLOW_IMAGE_NAME:-your_own_extending_airflow_image_name}

```

### 2. Run the image

If you are a cloud composer user,skip ths entire section and go to number 3.
To get airflow installed in your local machine,pelase run the code below

```sh
docker-compose up airflow-init
```
Once it returns a message "exists with code 0", your installation is successful.
Start your airflow with the code below

```sh
docker-compose up -d
```




### 4. Things to Remember

First, your service account key must be placed into the folder called `gcloud-key`. Make sure that your account can access all the listed services above. 

Second, if you visit the `schema` folder , you will see 6 json files and place them into the cloud storage.

```
<your_bucket_name>/schema
```
![image](https://user-images.githubusercontent.com/53164959/211186850-0db2d31d-7228-4f1a-bf51-d9c1998b4c72.png)
<p align='center'>Fig 2.Schema Infomration Stored in Cloud Storage</p>


Third,you need to create three connections in total to make the operation run. 

![image](https://user-images.githubusercontent.com/53164959/211187179-baa88193-a5ef-41f8-b5ed-9e289385bea4.png)
<p align='center'>Fig 3. Airflow Connections </p>


# 5. How to Run
Make sure Airflow webserver and scheduler is running. Open the Airflow UI `http://<compute-engine-instance-ip>:<config-port`.

We have two dags, one of which triggers the other once its work finshes without any errors. 

![image](https://user-images.githubusercontent.com/53164959/211186703-09813bf0-829b-41a2-8e2f-e8409c993d95.png)
<p align='center'>Fig 4. First Dag </p>

![image](https://user-images.githubusercontent.com/53164959/211187311-97969e1e-6414-4438-90b2-77469fad38e5.png)
<p align='center'>Fig 5. Second Dag </p>


![image](https://user-images.githubusercontent.co
