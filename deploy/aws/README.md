# AWS EC2 deployment

This guide deploys CertGen to one Ubuntu EC2 instance. Nginx serves the built React frontend and forwards API requests to Gunicorn. Flask and its in-process background worker run together, with SQLite and generated PDFs stored on the instance. This keeps the deployment small and avoids separate AWS database, storage, or load-balancer services.

The deployment is intended for a portfolio/demo workload. Certificate files and job records are kept on the instance and can be removed when the instance or its disk is deleted. There is no object-storage or backup setup in this design.

## Before launching

1. Check the AWS Billing console to confirm that the account's Free Tier plan and credits are still active. Credits are limited and can run out; monitor the balance and usage.
2. In EC2, select the Mumbai region (`ap-south-1`) and an Ubuntu Server 24.04 LTS image.
3. Choose a Free Tier-eligible `t3.micro` instance and the smallest supported general-purpose SSD root volume. Confirm the console labels the selected configuration as eligible before launch.
4. Create or select an SSH key pair and save its private key securely. Do not commit or upload the private key to GitHub.
5. Configure the security group to allow HTTP (port 80) from the internet and SSH (port 22) only from your current IP. Do not open the Flask port (8000) publicly.

AWS service eligibility and prices depend on the account plan and current usage. This guide does not guarantee zero charges. Do not add a load balancer, NAT Gateway, managed database, or other resources for this single-instance setup.

## Instance setup

Connect to the instance using the downloaded key and the `ubuntu` user. Then install the system packages:

```bash
sudo apt update
sudo apt install -y git nginx python3-venv python3-pip
```

Put the reviewed and pushed project version at `/opt/certgen`. If cloning the GitHub repository, use the repository's HTTPS URL and the branch that contains the deployment files:

```bash
sudo git clone --branch main https://github.com/shashwat124c/Certificate-Generator.git /opt/certgen
sudo chown -R root:root /opt/certgen
sudo chmod -R a+rX /opt/certgen
cd /opt/certgen
sudo python3 -m venv .venv
sudo .venv/bin/pip install -r requirements.txt
```

Build the React frontend from the project directory on a computer with Node.js and npm installed:

```powershell
cd frontend
npm ci
npm run build
```

Copy the resulting `frontend/dist` directory to `/opt/certgen/frontend/dist` on the EC2 instance. Keep the built frontend and backend from the same reviewed commit.

Create the unprivileged application account and writable data directory, then install the service and Nginx configuration:

```bash
sudo useradd --system --home-dir /var/lib/certgen --shell /usr/sbin/nologin certgen
sudo install -d -o certgen -g certgen /var/lib/certgen
sudo install -d -o certgen -g certgen /opt/certgen/instance
sudo install -m 0644 /opt/certgen/deploy/aws/certgen.env /etc/certgen.env
sudo install -m 0644 /opt/certgen/deploy/aws/certgen.service /etc/systemd/system/certgen.service
sudo install -m 0644 /opt/certgen/deploy/aws/nginx.conf /etc/nginx/sites-available/certgen
sudo ln -s /etc/nginx/sites-available/certgen /etc/nginx/sites-enabled/certgen
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now certgen
sudo systemctl enable --now nginx
```

Visit the instance's public address over HTTP. The React UI and API use the same origin, so no separate frontend API URL or cross-origin configuration is needed.

## Updating the deployment

Deploy only a reviewed, committed version. Update the source and React build together, then restart the service:

```bash
sudo systemctl restart certgen
sudo systemctl status certgen --no-pager
```

## Cost and cleanup

Check AWS Billing and Cost Management regularly. Credits can expire or be exhausted, and resources can become billable outside the account's Free Tier eligibility. When the demo is no longer needed, terminate the EC2 instance and remove any separately retained EBS volumes or snapshots. A stopped instance can still incur storage charges.
