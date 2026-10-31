# Three-Tier Application Deployment on Kubernetes Using Kind

## 1. Project Overview

This project demonstrates how to deploy a three-tier web application on a Kubernetes cluster using Kind (Kubernetes in Docker), hosted on an Amazon Linux EC2 instance.

The application consists of three independent tiers:

1. **Frontend:** Nginx serves a static HTML web application.
2. **Backend:** Python Flask provides REST API endpoints.
3. **Database:** MySQL stores application data.

Kubernetes manages the application containers, deployments, networking, services, and persistent storage.

### Project objectives

- Understand Kubernetes architecture and resources.
- Build Docker images for frontend and backend applications.
- Create a Kubernetes cluster using Kind.
- Deploy MySQL using StatefulSet and PersistentVolumeClaim.
- Deploy frontend and backend using Kubernetes Deployments.
- Configure Kubernetes Services for internal communication.
- Store database credentials using Kubernetes Secrets.
- Test communication between all three tiers.
- Access the frontend using the EC2 public IP and port forwarding.
- Manage the complete project using Git and GitHub.

## 2. Architecture

The application follows a three-tier architecture.

### Application traffic flow

1. A user opens the application through a web browser.
2. The browser connects to the EC2 public IP on port 8080.
3. Kubernetes port forwarding sends traffic to the frontend Service.
4. The frontend Service forwards traffic to an Nginx Pod.
5. Nginx serves the HTML page.
6. When the user requests backend data, Nginx forwards the API request to the backend Service.
7. The backend Service forwards the request to a Flask Pod.
8. Flask connects to MySQL through the MySQL Service.
9. MySQL retrieves or stores application records.
10. Flask returns the result to the frontend.

### Architecture components

| Component | Technology | Purpose |
|---|---|---|
| Host | Amazon Linux EC2 | Runs Docker and Kind |
| Container runtime | Docker | Builds and runs containers |
| Kubernetes cluster | Kind | Provides Kubernetes environment |
| Frontend | Nginx | Serves HTML and proxies API requests |
| Backend | Python Flask | Provides REST APIs |
| Database | MySQL 8.0 | Stores application records |
| Networking | Kubernetes Services | Enables internal communication |
| Storage | PersistentVolumeClaim | Provides persistent database storage |
| Source control | GitHub | Stores project files and documentation |

## 3. Technologies Used

- Amazon Linux EC2
- Docker
- Kubernetes
- Kind
- kubectl
- Nginx
- Python Flask
- MySQL
- YAML
- Git
- GitHub

## 4. Project Directory Structure

The project is organized into three main folders:

- `backend/` – Backend application source code and Dockerfile.
- `frontend/` – Frontend HTML, Nginx configuration, and Dockerfile.
- `kubernetes/` – Kubernetes manifests for application resources.

The repository also contains:

- `README.md` – Project documentation.
- `.gitignore` – Prevents sensitive and unnecessary files from being committed.

## 5. Prerequisites

This project was performed on an Amazon Linux EC2 instance.

### Recommended EC2 configuration

| Configuration | Recommendation |
|---|---|
| Instance type | t3.medium or larger |
| CPU | 2 vCPUs or more |
| RAM | 4 GB or more |
| Storage | 20–30 GB |
| Operating system | Amazon Linux |
| Network | Internet access for downloading images and packages |

### Required tools

- Docker
- kubectl
- Kind
- Git

### Verify installed tools

Check Docker:

`docker --version`

Check kubectl:

`kubectl version --client`

Check Kind:

`kind version`

Check Git:

`git --version`

Check Docker service:

`sudo systemctl status docker`

If Docker is not running:

`sudo systemctl start docker`

Enable Docker at system startup:

`sudo systemctl enable docker`

Add the EC2 user to the Docker group:

`sudo usermod -aG docker ec2-user`

Refresh group membership:

`newgrp docker`

Verify Docker access:

`docker ps`

## 6. Create the Kind Kubernetes Cluster

Kind creates a Kubernetes cluster using Docker containers.

Create a cluster named `three-tier`:

`kind create cluster --name three-tier`

Verify the cluster:

`kind get clusters`

Check Kubernetes nodes:

`kubectl get nodes`

Check the active Kubernetes context:

`kubectl config current-context`

Expected context:

`kind-three-tier`

The Kind cluster runs inside Docker on the EC2 instance.

## 7. Create Project Directories

Create the project root directory:

`mkdir -p ~/three-tier-app`

Create the backend directory:

`mkdir -p ~/three-tier-app/backend`

Create the frontend directory:

`mkdir -p ~/three-tier-app/frontend`

Create the Kubernetes directory:

`mkdir -p ~/three-tier-app/kubernetes`

Move into the project directory:

`cd ~/three-tier-app`

Verify the directory structure:

`ls -R`

## 8. Backend Application

The backend is developed using Python Flask.

It provides the following REST API endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Returns the application health status |
| `/api` | GET | Returns a backend response |
| `/api/users` | GET | Retrieves users from MySQL |
| `/api/users` | POST | Inserts a new user into MySQL |

### Backend components

**app.py**

Contains the Flask application, API endpoints, database connection logic, and SQL operations.

**requirements.txt**

Contains the Python dependencies required by the application, including Flask and the MySQL connector.

**Dockerfile**

Defines how the backend application is packaged into a Docker image.

### Backend configuration

The backend receives its database configuration through environment variables:

- `DB_HOST` – MySQL Kubernetes Service name.
- `DB_NAME` – Database name.
- `DB_USER` – Database username.
- `DB_PASSWORD` – Database password.

The backend uses `mysql-service` as its database hostname.

## 9. Frontend Application

The frontend uses HTML, JavaScript, and Nginx.

The web page provides two main functions:

1. **Check Backend:** Calls the Flask API and displays the response.
2. **Get Users:** Retrieves user records from the MySQL database through the backend.

### Frontend components

**index.html**

Contains the user interface, buttons, and JavaScript functions.

**nginx.conf**

Configures Nginx to serve the frontend and forward API requests to the backend Kubernetes Service.

**Dockerfile**

Defines how the frontend application and Nginx configuration are packaged into a Docker image.

### Nginx reverse proxy

Nginx forwards requests beginning with `/api` to:

`http://backend-service:5000`

Kubernetes DNS resolves `backend-service` to the backend Service.

This means the frontend does not need to know the individual backend Pod IP addresses.

## 10. Build Docker Images

Docker images package the application and its dependencies.

### 10.1 Build Backend Image

Move into the backend directory:

`cd ~/three-tier-app/backend`

Build the image:

`docker build -t three-tier-backend:v1 .`

Verify:

`docker images | grep three-tier`

### 10.2 Build Frontend Image

Move into the frontend directory:

`cd ~/three-tier-app/frontend`

Build the frontend image:

`docker build -t three-tier-frontend:v3 .`

The `v3` image contains the corrected Nginx configuration.

Verify:

`docker images | grep three-tier`

### 10.3 Load Images into Kind

Kind runs Kubernetes nodes as Docker containers. Images built on the EC2 host must be loaded into the Kind cluster.

Load the backend image:

`kind load docker-image three-tier-backend:v1 --name three-tier`

Load the frontend image:

`kind load docker-image three-tier-frontend:v3 --name three-tier`

Verify local images:

`docker images`

## 11. Create Kubernetes Namespace

A Namespace is a logical separation of resources inside a Kubernetes cluster.

In this project, all application resources are deployed in the `three-tier` namespace.

The namespace manifest is stored in:

`kubernetes/namespace.yaml`

Apply the namespace:

`kubectl apply -f ~/three-tier-app/kubernetes/namespace.yaml`

Verify:

`kubectl get namespaces`

Check application resources:

`kubectl get all -n three-tier`

## 12. Create Kubernetes Secret

A Kubernetes Secret stores sensitive configuration such as database credentials.

The MySQL credentials are supplied through a Kubernetes Secret named `mysql-secret`.

Create the Secret:

`kubectl create secret generic mysql-secret --namespace three-tier --from-literal=MYSQL_ROOT_PASSWORD='YOUR_MYSQL_ROOT_PASSWORD' --from-literal=MYSQL_DATABASE='appdb' --from-literal=MYSQL_USER='appuser' --from-literal=MYSQL_PASSWORD='YOUR_MYSQL_PASSWORD'`

Replace the placeholders with your own lab passwords.

Verify the Secret:

`kubectl get secrets -n three-tier`

Describe the Secret without displaying its values:

`kubectl describe secret mysql-secret -n three-tier`

The MySQL and backend manifests reference this Secret by name.

**Security note:** Do not commit real passwords or Kubernetes Secret manifests containing credentials to GitHub. Kubernetes Secret values are base64-encoded by default, not automatically encrypted in every storage configuration. Use appropriate encryption, RBAC, and an external secrets solution for production.

## 13. Deploy MySQL Using StatefulSet

MySQL is a stateful application because it stores persistent data.

This project uses:

- StatefulSet to manage the MySQL Pod.
- PersistentVolumeClaim to request persistent storage.
- Headless Service to provide stable network identity.
- Kubernetes Secret to supply database credentials.

The MySQL manifest is stored in:

`kubernetes/mysql.yaml`

Apply the MySQL configuration:

`kubectl apply -f ~/three-tier-app/kubernetes/mysql.yaml`

Verify the StatefulSet:

`kubectl get statefulsets -n three-tier`

Verify the MySQL Pod:

`kubectl get pods -n three-tier`

Verify PersistentVolumeClaims:

`kubectl get pvc -n three-tier`

Verify Services:

`kubectl get svc -n three-tier`

Wait until:

- The MySQL Pod is `Running`.
- The PVC status is `Bound`.

### 13.1 Create the users table

Connect to MySQL:

`kubectl exec -it mysql-0 -n three-tier -- mysql -uappuser -p`

Enter the MySQL password configured in the Secret.

Select the database:

`USE appdb;`

Create the users table:

`CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(100) NOT NULL);`

Insert sample records:

`INSERT INTO users (name, email) VALUES ('John', 'john@example.com'), ('Alice', 'alice@example.com');`

Verify the records:

`SELECT * FROM users;`

Exit MySQL:

`exit`

## 14. Deploy the Backend

The backend is deployed using a Kubernetes Deployment with two replicas.

The backend manifest is stored in:

`kubernetes/backend.yaml`

The Deployment:

- Creates two Flask backend Pods.
- Uses the backend Docker image.
- Exposes container port 5000.
- Receives database configuration through environment variables.
- References the Kubernetes Secret for database credentials.

The backend Service:

- Is named `backend-service`.
- Uses ClusterIP networking.
- Exposes port 5000.
- Selects Pods using the backend application label.

Apply the backend manifest:

`kubectl apply -f ~/three-tier-app/kubernetes/backend.yaml`

Verify the Deployment:

`kubectl get deployments -n three-tier`

Verify Pods:

`kubectl get pods -n three-tier`

Verify Services:

`kubectl get svc -n three-tier`

Expected backend Deployment status:

`backend   2/2`

### 14.1 Test the Backend API

Forward the backend Service port:

`kubectl port-forward svc/backend-service 5000:5000 -n three-tier`

Keep the port-forward process running.

Open another EC2 terminal and test:

`curl http://localhost:5000/api`

Expected response:

`{"database":"mysql-service","message":"Hello from the backend!"}`

Test the database connection through the backend:

`curl http://localhost:5000/api/users`

Expected response contains the sample John and Alice records.

This confirms that the Flask backend can communicate with MySQL.

Stop the port-forward process using `Ctrl+C` after testing.

## 15. Deploy the Frontend

The frontend is deployed using a Kubernetes Deployment with two replicas.

The frontend manifest is stored in:

`kubernetes/frontend.yaml`

The Deployment:

- Creates two Nginx frontend Pods.
- Uses the frontend Docker image.
- Exposes container port 80.

The frontend Service:

- Is named `frontend-service`.
- Uses ClusterIP networking.
- Exposes port 80.
- Selects frontend Pods using labels.

Apply the frontend manifest:

`kubectl apply -f ~/three-tier-app/kubernetes/frontend.yaml`

Verify the Deployment:

`kubectl get deployments -n three-tier`

Verify Pods:

`kubectl get pods -n three-tier`

Verify Services:

`kubectl get svc -n three-tier`

Expected workload status:

| Component | Desired replicas | Ready replicas |
|---|---:|---:|
| Frontend | 2 | 2 |
| Backend | 2 | 2 |
| MySQL | 1 | 1 |

All application Pods should be in `Running` status.

## 16. Expose the Frontend

The frontend Service uses ClusterIP networking.

ClusterIP Services are accessible only inside the Kubernetes cluster.

For this lab, the frontend is exposed through `kubectl port-forward`.

Run:

`kubectl port-forward --address 0.0.0.0 svc/frontend-service 8080:80 -n three-tier`

### Command explanation

- `kubectl port-forward` establishes a connection between a local port and a Kubernetes resource.
- `--address 0.0.0.0` makes the forwarding listener available on all EC2 network interfaces.
- `svc/frontend-service` identifies the frontend Service.
- `8080:80` maps EC2 port 8080 to frontend Service port 80.
- `-n three-tier` specifies the Kubernetes namespace.

Keep this terminal open while accessing the application.

### 16.1 Configure the EC2 Security Group

In the AWS Console:

1. Open EC2.
2. Select the EC2 instance.
3. Open its Security Group.
4. Select Edit inbound rules.
5. Add a custom TCP inbound rule.

| Setting | Value |
|---|---|
| Type | Custom TCP |
| Protocol | TCP |
| Port | 8080 |
| Source | Your public IP address `/32` |

Avoid exposing the lab application to everyone on the internet.

### 16.2 Access the Application

Find the public IPv4 address of your EC2 instance.

Open the following address in your browser:

`http://YOUR_EC2_PUBLIC_IP:8080`

Replace the placeholder with the actual EC2 public IP.

The frontend should display the Three-Tier Kubernetes Application.

Test the following buttons:

**Check Backend**

This calls the Flask backend API and displays the response.

**Get Users**

This calls the backend API, retrieves the MySQL records, and displays them on the frontend.

The port-forward process must remain running while accessing the application.

## 17. Final Verification

Check all application resources:

`kubectl get all -n three-tier`

Check persistent storage:

`kubectl get pvc -n three-tier`

Check Services:

`kubectl get svc -n three-tier`

Check Deployments:

`kubectl get deployments -n three-tier`

Check StatefulSets:

`kubectl get statefulsets -n three-tier`

Check Kubernetes nodes:

`kubectl get nodes`

Expected application workload:

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

Possible reason: Kubernetes cannot find or download the required Docker image.

Check:

`kubectl describe pod POD_NAME -n three-tier`

Load the backend image into Kind:

`kind load docker-image three-tier-backend:v1 --name three-tier`

Load the frontend image into Kind:

`kind load docker-image three-tier-frontend:v3 --name three-tier`

Ensure the image names and tags in the Kubernetes manifests match the loaded images.

### Issue 2: CrashLoopBackOff or Error

Possible reason: The application container starts but exits due to an application or configuration error.

Check logs:

`kubectl logs POD_NAME -n three-tier`

Describe the Pod:

`kubectl describe pod POD_NAME -n three-tier`

For frontend Nginx errors, verify the Nginx configuration and rebuild the frontend image after correcting it.

### Issue 3: MySQL Pod is Pending

Check:

`kubectl get pvc -n three-tier`

Describe the PVC:

`kubectl describe pvc mysql-storage-mysql-0 -n three-tier`

Verify that the PVC is bound and that the cluster has sufficient storage resources.

### Issue 4: Backend Cannot Connect to MySQL

Check Pods:

`kubectl get pods -n three-tier`

Check Services:

`kubectl get svc -n three-tier`

Check backend logs:

`kubectl logs deployment/backend -n three-tier`

Verify the Secret exists:

`kubectl get secret mysql-secret -n three-tier`

Verify that the `users` table exists in the `appdb` database.

### Issue 5: Nginx Configuration Error

Check frontend logs:

`kubectl logs deployment/frontend -n three-tier`

Verify the Nginx configuration.

After making corrections, rebuild the frontend image using a new version, load the image into Kind, and update the Deployment.

### Issue 6: Frontend Not Accessible Through Public IP

Check that port forwarding is running:

`kubectl port-forward --address 0.0.0.0 svc/frontend-service 8080:80 -n three-tier`

Test locally on EC2:

`curl http://localhost:8080`

Verify that:

- The EC2 Security Group allows inbound TCP 8080 from your public IP.
- The instance has a public IPv4 address.
- The instance has an appropriate internet gateway route.
- The frontend Pods are running.
- The port-forward process is still active.

**Important:** Kind runs inside Docker. A Kubernetes NodePort is not automatically reachable through the EC2 host's public IP. Port forwarding is used in this project instead.

## 19. Cleanup

Stop the port-forward process using `Ctrl+C`.

Delete the frontend resources:

`kubectl delete -f ~/three-tier-app/kubernetes/frontend.yaml`

Delete the backend resources:

`kubectl delete -f ~/three-tier-app/kubernetes/backend.yaml`

Delete the MySQL resources:

`kubectl delete -f ~/three-tier-app/kubernetes/mysql.yaml`

Delete the Kubernetes Secret:

`kubectl delete secret mysql-secret -n three-tier`

Delete the namespace:

`kubectl delete namespace three-tier`

**Warning:** Deleting the MySQL StatefulSet and PVC may result in data loss. Back up important data before cleanup.

To delete the entire Kind cluster:

`kind delete cluster --name three-tier`

## 20. Kubernetes Concepts Learned

| Kubernetes concept | Application in this project |
|---|---|
| Cluster | Runs the complete application |
| Node | Kind control-plane container |
| Namespace | Separates application resources |
| Pod | Runs application containers |
| Deployment | Manages frontend and backend replicas |
| StatefulSet | Manages the MySQL database |
| Service | Provides stable internal networking |
| ClusterIP | Allows internal Service communication |
| Headless Service | Provides stable MySQL network identity |
| Secret | Supplies database credentials |
| PersistentVolumeClaim | Requests persistent database storage |
| Container Image | Packages application code and dependencies |
| Port Forwarding | Exposes the frontend for lab access |

## 21. Future Improvements

Possible improvements include:

- Add Kubernetes readiness and liveness probes.
- Add CPU and memory requests and limits.
- Add ConfigMaps for non-sensitive configuration.
- Add an Ingress Controller.
- Add HTTPS using TLS.
- Add Horizontal Pod Autoscaler.
- Add Helm charts.
- Add GitHub Actions CI/CD.
- Deploy the application on Amazon EKS.
- Use Amazon RDS instead of a MySQL container.
- Use AWS Secrets Manager for sensitive credentials.
- Add monitoring with Prometheus and Grafana.

## 22. Conclusion

This project demonstrates a complete three-tier application deployed on Kubernetes using Kind.

The frontend, backend, and database run as separate Kubernetes workloads.

The frontend communicates with the backend through an internal Kubernetes Service. The backend communicates with MySQL through another Kubernetes Service. MySQL uses persistent storage to retain application data.

This hands-on project provides practical experience with:

- Docker image creation and management.
- Kubernetes cluster setup.
- Kubernetes Deployments and StatefulSets.
- Kubernetes Services and networking.
- Kubernetes Secrets.
- Persistent storage.
- Application communication.
- Public access through EC2 port forwarding.
- Git and GitHub source control.

**Project type:** Kubernetes hands-on practice  
**Environment:** Amazon Linux EC2 + Docker + Kind  
**Application:** Nginx + Python Flask + MySQL  
**Orchestration:** Kubernetes
