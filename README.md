# Three-Tier Application Deployment on Kubernetes using Kind

## 1. Project Overview

This project demonstrates how to deploy a three-tier web application on a local Kubernetes cluster running with Kind (Kubernetes in Docker) on an Amazon Linux EC2 instance.

The application consists of three layers:

1. **Frontend:** Nginx serves a static HTML web application.
2. **Backend:** Python Flask provides REST API endpoints.
3. **Database:** MySQL stores application data.

Kubernetes manages the application containers, deployments, services, networking, and database storage.

### Project objectives

- Understand Kubernetes architecture and resources.
- Build Docker images for frontend and backend applications.
- Create a Kubernetes cluster using Kind.
- Deploy a MySQL database using StatefulSet and PersistentVolumeClaim.
- Deploy backend and frontend applications using Deployments.
- Configure Kubernetes Services for internal communication.
- Store database credentials using Kubernetes Secrets.
- Test communication between all three tiers.
- Access the frontend using an EC2 public IP and port forwarding.

## 2. Architecture

```text
                  User / Web Browser
                         |
                         |
                 EC2 Public IP:8080
                         |
                  EC2 Security Group
                         |
                         |
             kubectl port-forward
                    8080 -> 80
                         |
                         |
                Frontend Service
                    ClusterIP
                         |
                         |
                 Frontend Pods
                  Nginx x 2
                         |
                         |
                Backend Service
                    ClusterIP
                         |
                         |
                 Backend Pods
                 Flask API x 2
                         |
                         |
                  MySQL Service
                         |
                         |
                  MySQL Pod
                  StatefulSet
                         |
                         |
                 Persistent Volume
                         |
                         |
                   MySQL Data
```

### Application communication

- The user accesses the frontend through a web browser.
- Nginx serves the frontend HTML page.
- When the user clicks **Check Backend**, Nginx forwards `/api` to the Flask backend.
- When the user clicks **Get Users**, Nginx forwards `/api/users` to Flask.
- Flask connects to MySQL through `mysql-service`.
- MySQL returns the records to Flask.
- Flask returns JSON data to the frontend.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Amazon Linux EC2 | Host machine |
| Docker | Container image building |
| Kind | Local Kubernetes cluster |
| Kubernetes | Container orchestration |
| kubectl | Kubernetes command-line management |
| Nginx | Frontend web server |
| Python Flask | Backend REST API |
| MySQL 8.0 | Database |
| YAML | Kubernetes configuration |
| Git and GitHub | Source code management |

## 4. Project Directory Structure

```text
three-tier-app/
│
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
│
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   └── nginx.conf
│
└── kubernetes/
    ├── namespace.yaml
    ├── mysql.yaml
    ├── mysql-secret.yaml
    ├── backend.yaml
    └── frontend.yaml
```

**Security note:** `mysql-secret.yaml` contains lab credentials and must not be committed to GitHub. The repository uses a Kubernetes Secret created separately.

## 5. Prerequisites

This project was performed on an Amazon Linux EC2 instance.

Required tools:

- Docker
- kubectl
- Kind
- Git
- An EC2 instance with sufficient memory

Recommended EC2 configuration for this practice:

- Instance type: t3.medium or larger
- RAM: 4 GB or more
- Storage: 20–30 GB
- Operating system: Amazon Linux

Verify the installed tools:

```bash
docker --version
```

```bash
kubectl version --client
```

```bash
kind version
```

```bash
git --version
```

Verify Docker is running:

```bash
sudo systemctl status docker
```

If Docker is not running:

```bash
sudo systemctl start docker
```

Enable Docker at startup:

```bash
sudo systemctl enable docker
```

Add the EC2 user to the Docker group:

```bash
sudo usermod -aG docker ec2-user
```

Refresh the group membership:

```bash
newgrp docker
```

Verify Docker access:

```bash
docker ps
```

## 6. Create the Kind Kubernetes Cluster

Kind creates a Kubernetes cluster using Docker containers.

Create a cluster named `three-tier`:

```bash
kind create cluster --name three-tier
```

Check the cluster:

```bash
kind get clusters
```

Check Kubernetes nodes:

```bash
kubectl get nodes
```

Check the current Kubernetes context:

```bash
kubectl config current-context
```

Expected context:

```text
kind-three-tier
```

The Kind cluster runs inside Docker on the EC2 instance.

## 7. Create the Project Directories

Create the project root:

```bash
mkdir -p ~/three-tier-app
```

Create application directories:

```bash
mkdir -p ~/three-tier-app/backend
```

```bash
mkdir -p ~/three-tier-app/frontend
```

```bash
mkdir -p ~/three-tier-app/kubernetes
```

Move into the project directory:

```bash
cd ~/three-tier-app
```

Verify the structure:

```bash
ls -R
```

## 8. Backend Application

The backend is developed using Python Flask.

It provides three main endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health response |
| `/api` | GET | Backend API response |
| `/api/users` | GET | Retrieve users from MySQL |
| `/api/users` | POST | Insert a user into MySQL |

### 8.1 Create app.py

```bash
vi ~/three-tier-app/backend/app.py
```

Application code:

```python
from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "mysql-service")
DB_NAME = os.environ.get("DB_NAME", "appdb")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "apppassword")


def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/api")
def api():
    return jsonify({
        "message": "Hello from the backend!",
        "database": DB_HOST
    })


@app.route("/api/users", methods=["GET"])
def get_users():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email FROM users")

    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return jsonify(users)


@app.route("/api/users", methods=["POST"])
def create_user():

    data = request.get_json()

    name = data["name"]
    email = data["email"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s)",
        (name, email)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return jsonify({
        "message": "User created successfully"
    }), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### Explanation

- Flask creates the REST API.
- `DB_HOST` identifies the MySQL Kubernetes Service.
- `DB_NAME` identifies the database.
- `DB_USER` and `DB_PASSWORD` provide database authentication.
- `/api` returns a backend response.
- `/api/users` retrieves records from MySQL.
- POST `/api/users` inserts a new user.

The database connection settings are supplied through environment variables in Kubernetes.

### 8.2 Create requirements.txt

```bash
vi ~/three-tier-app/backend/requirements.txt
```

Add:

```text
Flask==3.1.2
mysql-connector-python==9.4.0
```

These packages install Flask and the MySQL connector.

### 8.3 Create Backend Dockerfile

```bash
vi ~/three-tier-app/backend/Dockerfile
```

Add:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]
```

### Dockerfile explanation

- `FROM`: Selects the Python base image.
- `WORKDIR`: Sets the application working directory.
- `COPY`: Copies the requirements file into the image.
- `RUN`: Installs Python dependencies.
- `EXPOSE`: Documents the application port.
- `CMD`: Starts the Flask application.

## 9. Frontend Application

The frontend uses HTML, JavaScript, and Nginx.

### 9.1 Create index.html

```bash
vi ~/three-tier-app/frontend/index.html
```

Add:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Three Tier Kubernetes Application</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
        }

        .container {
            max-width: 700px;
            margin: auto;
        }

        button {
            padding: 10px 20px;
            margin-top: 10px;
        }

        #result {
            margin-top: 20px;
            padding: 15px;
            border: 1px solid #ccc;
        }
    </style>
</head>

<body>

<div class="container">

    <h1>Three-Tier Kubernetes Application</h1>

    <p>Frontend: Nginx</p>
    <p>Backend: Python Flask</p>
    <p>Database: MySQL</p>

    <button onclick="checkBackend()">Check Backend</button>
    <button onclick="getUsers()">Get Users</button>

    <div id="result">
        Click a button to test the application.
    </div>

</div>

<script>
async function checkBackend() {
    const response = await fetch("/api");
    const data = await response.json();
    document.getElementById("result").innerText =
        JSON.stringify(data, null, 2);
}

async function getUsers() {
    const response = await fetch("/api/users");
    const data = await response.json();
    document.getElementById("result").innerText =
        JSON.stringify(data, null, 2);
}
</script>

</body>
</html>
```

### 9.2 Create nginx.conf

```bash
vi ~/three-tier-app/frontend/nginx.conf
```

Add:

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend-service:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Nginx explanation

- Nginx listens on port 80.
- It serves the static frontend HTML.
- Requests to `/api` are forwarded to `backend-service`.
- Kubernetes DNS resolves `backend-service` to the backend Service IP.
- Nginx acts as a reverse proxy between the frontend and backend.

### 9.3 Create Frontend Dockerfile

```bash
vi ~/three-tier-app/frontend/Dockerfile
```

Add:

```dockerfile
FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

## 10. Build Docker Images

### 10.1 Build Backend Image

Move into the backend directory:

```bash
cd ~/three-tier-app/backend
```

Build the image:

```bash
docker build -t three-tier-backend:v1 .
```

Verify:

```bash
docker images | grep three-tier
```

### 10.2 Build Frontend Image

Move into the frontend directory:

```bash
cd ~/three-tier-app/frontend
```

Build the frontend image:

```bash
docker build -t three-tier-frontend:v3 .
```

The `v3` version contains the corrected Nginx configuration.

Verify:

```bash
docker images | grep three-tier
```

### 10.3 Load Images into Kind

Kind runs Kubernetes nodes as Docker containers. Images built on the EC2 host must be loaded into the Kind cluster.

Load backend:

```bash
kind load docker-image three-tier-backend:v1 --name three-tier
```

Load frontend:

```bash
kind load docker-image three-tier-frontend:v3 --name three-tier
```

Verify local Docker images:

```bash
docker images
```

## 11. Kubernetes Namespace

A Namespace is a logical separation of resources inside a Kubernetes cluster.

We use the namespace `three-tier` to keep all application resources together.

Create the namespace manifest:

```bash
vi ~/three-tier-app/kubernetes/namespace.yaml
```

Add:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: three-tier
```

Apply:

```bash
kubectl apply -f ~/three-tier-app/kubernetes/namespace.yaml
```

Verify:

```bash
kubectl get namespaces
```

All subsequent resources will be deployed in this namespace.

## 12. Create Kubernetes Secret

A Kubernetes Secret stores sensitive configuration such as database passwords.

Do not commit actual credentials to GitHub.

Create the namespace first, then create the Secret:

```bash
kubectl create secret generic mysql-secret \
  --namespace three-tier \
  --from-literal=MYSQL_ROOT_PASSWORD='rootpassword' \
  --from-literal=MYSQL_DATABASE='appdb' \
  --from-literal=MYSQL_USER='appuser' \
  --from-literal=MYSQL_PASSWORD='apppassword'
```

Verify:

```bash
kubectl get secrets -n three-tier
```

Describe the Secret without displaying its values:

```bash
kubectl describe secret mysql-secret -n three-tier
```

The MySQL and backend manifests refer to this Secret by name.

**Lab note:** Kubernetes Secret values are base64-encoded by default, not automatically encrypted in every storage configuration. Use appropriate encryption, access controls, and an external secrets solution for production.

## 13. Deploy MySQL Using StatefulSet

MySQL is a stateful application because it stores persistent data.

We use:

- StatefulSet to manage the MySQL Pod.
- PersistentVolumeClaim to request storage.
- Headless Service to provide stable network identity.
- Secret to provide database credentials.

Create the manifest:

```bash
vi ~/three-tier-app/kubernetes/mysql.yaml
```

Add:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-service
  namespace: three-tier
spec:
  selector:
    app: mysql
  ports:
    - port: 3306
      targetPort: 3306
  clusterIP: None

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: three-tier
spec:
  serviceName: mysql-service
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          ports:
            - containerPort: 3306
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: MYSQL_ROOT_PASSWORD
            - name: MYSQL_DATABASE
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: MYSQL_DATABASE
            - name: MYSQL_USER
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: MYSQL_USER
            - name: MYSQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: MYSQL_PASSWORD
          volumeMounts:
            - name: mysql-storage
              mountPath: /var/lib/mysql
  volumeClaimTemplates:
    - metadata:
        name: mysql-storage
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 2Gi
```

### Apply the MySQL configuration

```bash
kubectl apply -f ~/three-tier-app/kubernetes/mysql.yaml
```

Check the StatefulSet:

```bash
kubectl get statefulsets -n three-tier
```

Check the Pod:

```bash
kubectl get pods -n three-tier
```

Check PersistentVolumeClaims:

```bash
kubectl get pvc -n three-tier
```

Check Services:

```bash
kubectl get svc -n three-tier
```

Wait until the MySQL Pod is `Running` and its PVC is `Bound`.

### 13.1 Create the users table

Connect to MySQL:

```bash
kubectl exec -it mysql-0 -n three-tier -- mysql -uappuser -p
```

Enter the lab password:

```text
apppassword
```

Select the database:

```sql
USE appdb;
```

Create the table:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL
);
```

Insert sample records:

```sql
INSERT INTO users (name, email)
VALUES
('John', 'john@example.com'),
('Alice', 'alice@example.com');
```

Verify:

```sql
SELECT * FROM users;
```

Exit:

```sql
exit
```

## 14. Deploy the Backend

The backend runs two replicas of the Flask application.

Create the manifest:

```bash
vi ~/three-tier-app/kubernetes/backend.yaml
```

Add:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: three-tier
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: backend
          image: three-tier-backend:v1
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
          env:
            - name: DB_HOST
              value: "mysql-service"
            - name: DB_NAME
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: MYSQL_DATABASE
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: MYSQL_USER
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: MYSQL_PASSWORD

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: three-tier
spec:
  type: ClusterIP
  selector:
    app: backend
  ports:
    - port: 5000
      targetPort: 5000
      protocol: TCP
```

### Apply the backend manifest

```bash
kubectl apply -f ~/three-tier-app/kubernetes/backend.yaml
```

Verify:

```bash
kubectl get deployments -n three-tier
```

```bash
kubectl get pods -n three-tier
```

```bash
kubectl get svc -n three-tier
```

Expected backend replicas:

```text
backend   2/2
```

### 14.1 Test the backend

Forward the backend Service port:

```bash
kubectl port-forward svc/backend-service 5000:5000 -n three-tier
```

Open another EC2 terminal.

Test the API:

```bash
curl http://localhost:5000/api
```

Expected response:

```json
{
  "database": "mysql-service",
  "message": "Hello from the backend!"
}
```

Test the database through the backend:

```bash
curl http://localhost:5000/api/users
```

Expected response:

```json
[
  {
    "email": "john@example.com",
    "id": 1,
    "name": "John"
  },
  {
    "email": "alice@example.com",
    "id": 2,
    "name": "Alice"
  }
]
```

This confirms that the Flask backend can communicate with MySQL.

Stop the backend port-forward with `Ctrl+C` when finished.

## 15. Deploy the Frontend

The frontend uses Nginx and two replicas.

Create the manifest:

```bash
vi ~/three-tier-app/kubernetes/frontend.yaml
```

Add:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: three-tier
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: three-tier-frontend:v3
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: three-tier
spec:
  type: ClusterIP
  selector:
    app: frontend
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
```

### Apply the frontend manifest

```bash
kubectl apply -f ~/three-tier-app/kubernetes/frontend.yaml
```

Check the Deployment:

```bash
kubectl get deployments -n three-tier
```

Check the Pods:

```bash
kubectl get pods -n three-tier
```

Check the Services:

```bash
kubectl get svc -n three-tier
```

Expected application replicas:

```text
frontend   2/2
backend    2/2
mysql      1/1
```

## 16. Expose the Frontend

The frontend Service is configured as `ClusterIP`.

ClusterIP Services are reachable inside the Kubernetes cluster. They are not directly accessible through the EC2 public IP.

For this lab, we use `kubectl port-forward`.

Run:

```bash
kubectl port-forward --address 0.0.0.0 svc/frontend-service 8080:80 -n three-tier
```

Explanation:

- `kubectl port-forward`: Forwards a local port to a Kubernetes resource.
- `--address 0.0.0.0`: Listens on all EC2 network interfaces.
- `svc/frontend-service`: Selects the frontend Service.
- `8080:80`: Maps EC2 port 8080 to frontend Service port 80.
- `-n three-tier`: Specifies the application namespace.

Keep this terminal running.

### 16.1 Configure the EC2 Security Group

In the AWS Console:

1. Open EC2.
2. Select the instance.
3. Open its Security Group.
4. Select Edit inbound rules.
5. Add a custom TCP rule.

| Setting | Value |
|---|---|
| Type | Custom TCP |
| Protocol | TCP |
| Port | 8080 |
| Source | Your public IP address `/32` |

Do not expose the lab application to the entire internet unless you intentionally accept that risk.

### 16.2 Access the application

Open a browser:

```text
http://YOUR_EC2_PUBLIC_IP:8080
```

Replace `YOUR_EC2_PUBLIC_IP` with the actual public IPv4 address of your EC2 instance.

The frontend should display:

```text
Three-Tier Kubernetes Application

Frontend: Nginx
Backend: Python Flask
Database: MySQL

[Check Backend] [Get Users]
```

Click **Check Backend** to test the API.

Click **Get Users** to retrieve database records.

The port-forward process must remain running while using the page.

## 17. Final Verification

Run:

```bash
kubectl get all -n three-tier
```

Check persistent storage:

```bash
kubectl get pvc -n three-tier
```

Check the Services:

```bash
kubectl get svc -n three-tier
```

Check Deployments:

```bash
kubectl get deployments -n three-tier
```

Check the StatefulSet:

```bash
kubectl get statefulsets -n three-tier
```

Check the Kubernetes node:

```bash
kubectl get nodes
```

Expected workload:

| Component | Kubernetes resource | Replicas |
|---|---|---:|
| Frontend | Deployment | 2 |
| Backend | Deployment | 2 |
| MySQL | StatefulSet | 1 |
| Frontend networking | ClusterIP Service | 1 |
| Backend networking | ClusterIP Service | 1 |
| MySQL networking | Headless Service | 1 |
| MySQL storage | PVC | 1 |

## 18. Troubleshooting

### Issue 1: ImagePullBackOff

Check:

```bash
kubectl describe pod POD_NAME -n three-tier
```

Ensure the Docker image was loaded into Kind:

```bash
kind load docker-image three-tier-backend:v1 --name three-tier
```

```bash
kind load docker-image three-tier-frontend:v3 --name three-tier
```

Check that the image name in the Deployment matches the image tag.

### Issue 2: CrashLoopBackOff or Error

Check application logs:

```bash
kubectl logs POD_NAME -n three-tier
```

Describe the Pod:

```bash
kubectl describe pod POD_NAME -n three-tier
```

For frontend Nginx errors, check the Nginx configuration and its syntax.

### Issue 3: MySQL Pod is Pending

Check:

```bash
kubectl get pvc -n three-tier
```

```bash
kubectl describe pvc mysql-storage-mysql-0 -n three-tier
```

Check whether the PVC is bound and whether the Kind cluster has available storage.

### Issue 4: Backend cannot connect to MySQL

Check:

```bash
kubectl get pods -n three-tier
```

```bash
kubectl get svc -n three-tier
```

```bash
kubectl logs deployment/backend -n three-tier
```

Verify the database Secret exists:

```bash
kubectl get secret mysql-secret -n three-tier
```

Verify the `users` table exists in the `appdb` database.

### Issue 5: Nginx configuration error

Check:

```bash
kubectl logs deployment/frontend -n three-tier
```

The frontend image must contain the correct `nginx.conf`.

After changing Nginx configuration, rebuild the image using a new version, load it into Kind, and update the Deployment.

### Issue 6: Frontend is not reachable through the public IP

Check that port-forward is running:

```bash
kubectl port-forward --address 0.0.0.0 svc/frontend-service 8080:80 -n three-tier
```

Check locally:

```bash
curl http://localhost:8080
```

Check that the EC2 Security Group permits inbound TCP 8080 from your public IP.

Check that the EC2 instance has a public IPv4 address and that its network route permits internet traffic.

## 19. Cleanup

Stop the port-forward process using `Ctrl+C`.

Delete the application resources:

```bash
kubectl delete -f ~/three-tier-app/kubernetes/frontend.yaml
```

```bash
kubectl delete -f ~/three-tier-app/kubernetes/backend.yaml
```

```bash
kubectl delete -f ~/three-tier-app/kubernetes/mysql.yaml
```

Delete the Secret:

```bash
kubectl delete secret mysql-secret -n three-tier
```

Delete the namespace:

```bash
kubectl delete namespace three-tier
```

**Warning:** Deleting the MySQL StatefulSet and its PVC may result in data loss. This is a practice environment, so preserve or back up the data first if needed.

If you want to delete the entire Kind cluster:

```bash
kind delete cluster --name three-tier
```

## 20. Important Kubernetes Concepts Learned

| Kubernetes concept | How it is used in this project |
|---|---|
| Cluster | Runs the complete application |
| Node | Kind control-plane container |
| Namespace | Separates application resources |
| Pod | Runs application containers |
| Deployment | Manages frontend and backend replicas |
| StatefulSet | Manages MySQL |
| Service | Provides stable internal networking |
| ClusterIP | Allows internal service communication |
| Headless Service | Provides stable MySQL network identity |
| Secret | Supplies database credentials |
| PersistentVolumeClaim | Requests persistent database storage |
| Container Image | Packages application code and dependencies |
| Port Forwarding | Exposes the frontend for lab access |

## 21. Future Improvements

Possible improvements to this project:

- Add Kubernetes readiness and liveness probes.
- Add CPU and memory requests and limits.
- Add ConfigMaps for non-sensitive configuration.
- Add Ingress Controller.
- Add HTTPS using TLS.
- Add Horizontal Pod Autoscaler.
- Add Helm charts.
- Add GitHub Actions CI/CD.
- Use Amazon EKS instead of Kind.
- Use Amazon RDS instead of a MySQL container.
- Use AWS Secrets Manager for sensitive credentials.
- Add monitoring with Prometheus and Grafana.

## 22. Conclusion

This project demonstrates a complete three-tier application deployed on Kubernetes using Kind.

The frontend, backend, and database are deployed as separate Kubernetes workloads.

The frontend communicates with the backend through an internal Kubernetes Service. The backend communicates with MySQL through another Kubernetes Service. MySQL uses persistent storage to retain its data.

This practice project provides a foundation for understanding containerization, Kubernetes deployments, Services, StatefulSets, Secrets, storage, networking, and application deployment workflows.

---

**Project type:** Kubernetes hands-on practice  
**Environment:** Amazon Linux EC2 + Docker + Kind  
**Application:** Nginx + Python Flask + MySQL  
**Orchestration:** Kubernetes
