# 🚀 Zero-Downtime API Deployments with AWS API Gateway

> **Blue-Green + Canary Deployment Strategy using AWS Console**  
> Built by [Amit P M](https://github.com/Amitpm8) | [LinkedIn](https://www.linkedin.com/in/amitops)

---

## 📌 What This Project Is About

Imagine your app has 10,000 daily users. Your team ships a new version. How do you deploy it without:
- Taking the app offline (downtime)?
- Breaking things for everyone if the new version has a bug?
- Staying up at 2am manually watching logs?

This project solves exactly that using **two industry-standard deployment strategies** on AWS.

---

## 🧠 Core Concepts

### Blue-Green Deployment
```
Blue  = Current production (stable, v1.0.0)
Green = New version (v2.0.0, being tested)

Step 1: Run both simultaneously
Step 2: Test Green thoroughly
Step 3: Switch all traffic to Green
Step 4: Keep Blue on standby for instant rollback
```

### Canary Deployment
```
Instead of switching 100% traffic instantly:

10%  → send to Green, watch for errors
25%  → if fine, increase
50%  → still fine, increase
100% → fully promoted, Green is new production
```

> **Why "Canary"?** Coal miners used to bring canaries into mines. If toxic gas was present, the canary would show symptoms first — saving the miners. Same idea: send a small % of users to the new version first. If it breaks, only they're affected. Everyone else stays safe on Blue.

---

## 🏗️ Architecture

<img width="1187" height="947" alt="Screenshot 2026-05-07 221225" src="https://github.com/user-attachments/assets/26f1dc5c-15c0-4211-9300-85424bb0cfb5" />

## 🛠️ AWS Services Used

| Service | Role | Why |
|---|---|---|
| **Lambda** | Backend compute | Serverless, no servers to manage |
| **API Gateway** | Front door / router | Receives requests, routes to Lambda |
| **CloudWatch** | Monitoring | Detects errors automatically |
| **SNS** | Notifications | Sends email alerts when alarms fire |
| **IAM** | Permissions | Grants Lambda access to CloudWatch logs |

---

## 📋 Prerequisites

- AWS Account (Free Tier works)
- Basic understanding of AWS Console navigation
- An email address for alarm notifications

**Estimated Cost:** ~$0 on Free Tier for testing

---

## 🔐 Step 1: IAM Role (Lambda's Access Badge)

**Why this step?**  
Lambda needs permission to write logs to CloudWatch. Without an IAM Role, Lambda is a stranger with no access badge — AWS denies everything by default. This is the **Principle of Least Privilege (PoLP)** — give only the minimum permissions required, nothing more.

**What we create:**  
A role named `api-deployment-lambda-role` with only `AWSLambdaBasicExecutionRole` policy attached.

```
IAM → Roles → Create Role
  Trusted entity: AWS Service → Lambda
  Permission:     AWSLambdaBasicExecutionRole
  Role name:      api-deployment-lambda-role
```

**Key concept:**  
`AWSLambdaBasicExecutionRole` gives Lambda exactly one capability — write logs to CloudWatch. Nothing else. This is intentional.

---

## ⚡ Step 2: Blue Lambda — Production Version (v1.0.0)

**Why this step?**  
Lambda is our kitchen — it does the actual work. Blue Lambda represents the **current stable production version** that real users depend on. We never touch this during deployment.

```
Lambda → Create Function → Author from scratch
  Function name: blue-api-function
  Runtime:       Python 3.12
  Execution role: api-deployment-lambda-role (existing)
```

**Function Code:**
```python
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'Hello from Blue environment!',
            'version': 'v1.0.0',
            'environment': 'blue'
        })
    }
```

**Understanding the code:**
```
event   = the incoming request (URL, method, headers, body)
context = AWS metadata about this execution (request ID, timeout remaining)
```

**Deploy** the function after pasting code.

---

## 🟢 Step 3: Green Lambda — New Version (v2.0.0)

**Why this step?**  
Green Lambda is our **new version under testing**. It runs completely separately from Blue — users on production never hit this until we deliberately send them there. Same setup as Blue, different code.

```
Lambda → Create Function → Author from scratch
  Function name: green-api-function
  Runtime:       Python 3.12
  Execution role: api-deployment-lambda-role (existing)
```

**Function Code:**
```python
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'Hello from Green environment!',
            'version': 'v2.0.0',
            'environment': 'green',
            'new_feature': 'Enhanced response format'
        })
    }
```

**Deploy** the function after pasting code.

---

## 🚪 Step 4: API Gateway — The Front Door

**Why this step?**  
Lambda functions are sitting idle — no one can reach them from the internet. API Gateway acts as the **managed reverse proxy** — it receives all user requests and routes them to the right Lambda. Think of it like Nginx, but fully managed by AWS with built-in auth, throttling, and monitoring.

### 4a. Create the API
```
API Gateway → Create API → REST API → Build
  API name:    advanced-deployment-api
  Endpoint:    Regional
```

### 4b. Create /hello Resource
```
Actions → Create Resource
  Resource Name: hello
  Resource Path: hello   ← (API Gateway auto-adds the /)
```

### 4c. Create GET Method
```
Click /hello → Actions → Create Method → GET
  Integration type:  Lambda Function
  Lambda Function:   blue-api-function
```
Click **OK** when prompted for Lambda permission.

### 4d. Deploy to Production Stage
```
Actions → Deploy API
  Deployment stage: [New Stage]
  Stage name:       production
```

After deploying, copy your **Invoke URL**:
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/production
```

**Test it:**
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/production/hello
```

**Expected response:**
```json
{
    "message": "Hello from Blue environment!",
    "version": "v1.0.0",
    "environment": "blue"
}
```

---

## 🧪 Step 5: Staging Stage — Safe Testing Ground

**Why this step?**  
Before sending any real users to Green, we test it in complete isolation. Staging is a **separate environment** on the same API — real users never know it exists.

### 5a. Update Integration to Green
```
Click /hello → GET → Integration Request
  Lambda Function: green-api-function
```
Save → OK on permissions popup.

### 5b. Grant API Gateway Permission to Invoke Green Lambda
```
Lambda → green-api-function → Configuration → Permissions
  → Resource-based policy statements → Add permissions
    Principal:    apigateway.amazonaws.com
    Action:       lambda:InvokeFunction
    Statement ID: api-gateway-green
```

### 5c. Deploy to Staging Stage
```
Actions → Deploy API
  Deployment stage: [New Stage]
  Stage name:       staging
```

**Test staging:**
```
https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/staging/hello
```

**Expected response:**
```json
{
    "message": "Hello from Green environment!",
    "version": "v2.0.0",
    "environment": "green",
    "new_feature": "Enhanced response format"
}
```

Now you have:
```
production/hello → Blue v1.0.0 (real users) ✅
staging/hello    → Green v2.0.0 (testing)   ✅
```

---

## 🐦 Step 6: Canary Deployment — Gradual Traffic Shifting

**Why this step?**  
Staging passed. But staging traffic isn't real. Real users behave differently — different devices, edge cases, load patterns. Canary lets us send **10% of real production traffic** to Green first, watch for issues, then gradually increase.

```
API Gateway → Stages → production → Canary tab
  → Create Canary
    Percentage: 10
```

Then redeploy:
```
Actions → Deploy API → production → Deploy
```

**Traffic distribution:**
```
1000 users hit your API
├── 900 users → Blue v1.0.0 (safe)
└── 100 users → Green v2.0.0 (canary testing)
```

### Canary Promotion Path (if Green is healthy):
```
10% → wait, monitor → 25% → wait, monitor → 50% → wait, monitor → 100%
```

### Rollback Path (if something breaks):
```
1. Get CloudWatch alarm email
2. API Gateway → Stages → production → Canary tab
3. Set percentage back to 0
4. Deploy API to production
5. 100% users back on Blue instantly ✅
6. Fix Green calmly
```

### Final Promotion (when confident):
```
Canary tab → "Promote Canary"
→ Green becomes the new production
→ Blue kept as standby for next cycle
```

---

## 📊 Step 7: CloudWatch Alarms — Automated Problem Detection

**Why this step?**  
You can't watch dashboards 24/7. CloudWatch monitors your API health automatically and emails you the moment something breaks. Two alarms cover the two failure modes:

| Alarm | Metric | Threshold | Meaning |
|---|---|---|---|
| 5XX Errors | Server errors | > 5 in 5 min | Your Lambda/code crashed |
| 4XX Errors | Client errors | > 10 in 5 min | Bad requests, auth failures |

**5XX is the critical one for deployments** — it means YOUR new code (Green) is broken.

### Create 5XX Alarm:
```
CloudWatch → Alarms → Create Alarm → Select Metric
  AWS/ApiGateway → By Api Name → 5XXError
  Period:     5 minutes
  Threshold:  Greater than 5
  Action:     Create SNS topic → your@email.com
  Alarm name: api-5xx-errors-alarm
```

### Create 4XX Alarm:
```
Same steps, select 4XXError metric
  Threshold:  Greater than 10
  Alarm name: api-4xx-errors-alarm
```

**Confirm your email subscription** from the AWS notification email.

---

## ✅ Validation Checklist

```
□ IAM Role created with least privilege
□ Blue Lambda deployed and returning v1.0.0
□ Green Lambda deployed and returning v2.0.0
□ API Gateway created with /hello resource
□ Production stage → Blue Lambda responding ✅
□ Staging stage → Green Lambda responding ✅
□ Canary set to 10% on production
□ CloudWatch 5XX alarm → OK state
□ CloudWatch 4XX alarm → OK state
□ SNS email subscription confirmed
```

---

## 🔄 Complete Deployment Workflow

```
Developer ships new code (Green v2.0.0)
          ↓
Deploy to staging → test thoroughly
          ↓
Enable canary → 10% real traffic to Green
          ↓
Monitor CloudWatch for 15-30 minutes
          ↓
     ┌────┴────┐
   Errors?   All good?
     ↓           ↓
  Rollback   Increase to 25%
  to Blue         ↓
              Monitor again
                  ↓
              50% → 100%
                  ↓
           Promote Canary
                  ↓
         Green = New Production ✅
```

---

## 🧹 Cleanup (Avoid Ongoing Charges)

```
1. API Gateway → delete advanced-deployment-api
2. Lambda → delete blue-api-function
3. Lambda → delete green-api-function
4. CloudWatch → delete both alarms
5. IAM → detach policy → delete api-deployment-lambda-role
6. SNS → delete topics
```

---

## 🔮 Next Implementations

- [ ] **Automate rollback** using Lambda + CloudWatch Alarm trigger (no manual intervention at 2am)
- [ ] **GitHub Actions CI/CD** — auto deploy Green on every git push to main
- [ ] **Terraform** — provision this entire infrastructure as code (IaC)
- [ ] **Multi-region deployment** — Route 53 weighted routing across us-east-1 + ap-south-1
- [ ] **Custom domain** with AWS Certificate Manager SSL

---

## 💡 Key DevOps Concepts Practiced

| Concept | Applied Where |
|---|---|
| **Zero Downtime Deployment** | Blue-Green strategy |
| **Principle of Least Privilege** | IAM Role with minimal permissions |
| **Observability** | CloudWatch alarms + SNS notifications |
| **Risk Mitigation** | Canary gradual traffic shifting |
| **Rollback Strategy** | Instant Blue restore via Canary delete |
| **Environment Isolation** | Production vs Staging stages |

---

## 📁 Repository Structure

```
advanced-api-deployment/
├── README.md
└── src/
    ├── blue-function.py    ← Production Lambda (v1.0.0)
    └── green-function.py   ← New version Lambda (v2.0.0)
```

---

*Built as part of hands-on AWS DevOps portfolio — [github.com/Amitpm8](https://github.com/Amitpm8)*
