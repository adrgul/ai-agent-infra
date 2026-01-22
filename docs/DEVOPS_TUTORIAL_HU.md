# DevOps Deployment Pipeline Oktató Útmutató

## Tartalomjegyzék
1. [AWS Alapok - Mi az AWS és hogyan működik](#aws-alapok---mi-az-aws-és-hogyan-működik)
2. [Bevezetés](#bevezetés)
3. [Technológiai Áttekintés](#technológiai-áttekintés)
4. [Kódminták és Konfiguráció](#kódminták-és-konfiguráció)
5. [Platform Migrálás](#platform-migrálás)
6. [Gyakorlati Feladatok](#gyakorlati-feladatok)

---

## AWS Alapok - Mi az AWS és hogyan működik

### Mi az Amazon Web Services (AWS)?

Az **Amazon Web Services (AWS)** a világ vezető felhőszolgáltatási platformja, amelyet az Amazon üzemeltet. Az AWS több mint 200 különböző szolgáltatást kínál, amelyek lefedik szinte minden IT infrastruktúra igényt - a számítási kapacitástól kezdve az adatbázis-kezelésig, a gépi tanulástól a biztonsági megoldásokig.

#### Miért használunk felhőszolgáltatásokat?

**Hagyományos infrastruktúra (On-Premise):**
```
❌ Nagy kezdeti beruházás (szerverek vásárlása)
❌ Fizikai datacenter fenntartása
❌ Hardver karbantartás és frissítés
❌ Nehéz skálázhatóság
❌ Kapacitás tervezés (ki nem használt erőforrások)
```

**Felhő alapú infrastruktúra (AWS):**
```
✅ Pay-as-you-go (csak annyit fizetsz, amennyit használsz)
✅ Nincs fizikai hardver fenntartás
✅ Automatikus skálázás (scale up/down)
✅ Globális elérhetőség (availability zones, regions)
✅ Magas rendelkezésre állás beépítve
✅ Gyors kiépítés (perc alatt új szerverek)
```

---

### AWS Erőforrások Osztályozása

Az AWS szolgáltatásokat több szempont szerint osztályozhatjuk:

#### 1. **Szolgáltatási kategóriák szerint**

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS SZOLGÁLTATÁSOK                       │
└─────────────────────────────────────────────────────────────┘

📦 COMPUTE (Számítási kapacitás)
├── EC2: Virtual szerverek
├── ECS: Konténer orchestration
├── Lambda: Serverless functions
└── Fargate: Serverless konténerek

💾 STORAGE (Tárolás)
├── S3: Object storage (fájlok)
├── EBS: Block storage (VM disk-ek)
├── EFS: File system
└── Glacier: Archív tárolás

🗄️ DATABASE (Adatbázis)
├── RDS: Relational DB (MySQL, PostgreSQL)
├── DynamoDB: NoSQL key-value store
├── ElastiCache: In-memory cache (Redis, Memcached)
└── Aurora: High-performance relational DB

🌐 NETWORKING (Hálózat)
├── VPC: Virtual Private Cloud
├── Route 53: DNS szolgáltatás
├── CloudFront: CDN (Content Delivery Network)
└── API Gateway: API menedzsment

🔐 SECURITY & IDENTITY (Biztonság)
├── IAM: Identity and Access Management
├── Secrets Manager: Jelszavak, API kulcsok tárolása
├── KMS: Titkosítási kulcs kezelés
└── WAF: Web Application Firewall

📊 MONITORING & MANAGEMENT (Megfigyelés)
├── CloudWatch: Logging és monitoring
├── CloudTrail: API audit log
├── X-Ray: Distributed tracing
└── Systems Manager: Infrastruktúra menedzsment

🚀 DEVELOPER TOOLS (Fejlesztői eszközök)
├── CodePipeline: CI/CD pipeline
├── CodeBuild: Build szolgáltatás
├── CodeDeploy: Deployment automation
└── ECR: Docker registry

🤖 AI/ML (Mesterséges Intelligencia)
├── SageMaker: ML modellek training
├── Rekognition: Képfelismerés
├── Comprehend: Natural language processing
└── Bedrock: Generative AI
```

---

#### 2. **Menedzsment szint szerint**

##### **IaaS (Infrastructure as a Service)**
- **Mit kapsz**: Virtuális szerverek, hálózat, tárolás
- **Példák**: EC2, VPC, EBS
- **Felelősség**: Te kezeled az OS-t, alkalmazásokat, security patch-eket
- **Kontroll**: Magas
- **Használat**: Amikor teljes kontrollt akarsz

##### **PaaS (Platform as a Service)**
- **Mit kapsz**: Futtatási platform alkalmazásokhoz
- **Példák**: Elastic Beanstalk, RDS, ECS
- **Felelősség**: AWS kezeli az OS-t, te az alkalmazást
- **Kontroll**: Közepes
- **Használat**: Alkalmazás fejlesztés gyorsítása

##### **SaaS (Software as a Service)**
- **Mit kapsz**: Kész szoftver megoldás
- **Példák**: Amazon WorkDocs, Amazon Chime
- **Felelősség**: AWS kezeli az egészet
- **Kontroll**: Alacsony
- **Használat**: Kész funkciók használata

##### **FaaS (Function as a Service) / Serverless**
- **Mit kapsz**: Kód futtatás szerver nélkül
- **Példák**: Lambda, Fargate, DynamoDB
- **Felelősség**: Csak a kódodért felelsz
- **Kontroll**: Minimális
- **Használat**: Event-driven architektúrák

```
Kontroll és Felelősség

IaaS    [████████████████████] - Teljes kontroll
PaaS    [████████████░░░░░░░░] - Közepes kontroll
FaaS    [██████░░░░░░░░░░░░░░] - Minimális kontroll
SaaS    [████░░░░░░░░░░░░░░░░] - Csak használat
```

---

#### 3. **Számlázási modell szerint**

##### **On-Demand (Igény szerint)**
- Fizetsz annyit, amennyit használsz
- Nincs előzetes kötelezettség
- Legdrágább óradíj
- **Használat**: Nem előrejelezhető terhelés

##### **Reserved Instances (Fenntartott példányok)**
- 1 vagy 3 éves kötelezettségvállalás
- Akár 75% megtakarítás
- Előre fizetsz
- **Használat**: Stabil, előrejelezhető terhelés

##### **Spot Instances**
- Akár 90% kedvezmény
- AWS bármikor visszaveheti
- **Használat**: Fault-tolerant, batch feldolgozás

##### **Savings Plans**
- Rugalmas árazás
- Kötelezettségvállalás óránkénti költségre
- **Használat**: Vegyes workload-ok

---

### AWS Erőforrások ebben az Alkalmazásban

Ebben a projektben a következő AWS szolgáltatásokat használjuk:

#### **Compute (Számítási kapacitás)**

```
┌─────────────────────────────────────────────────────────┐
│  ECS (Elastic Container Service) + Fargate             │
│  ─────────────────────────────────────────────────────  │
│  Típus: PaaS/FaaS (Serverless konténerek)              │
│  Költség: Pay-per-use (vCPU + RAM óránként)            │
│  Használat: AI Agent alkalmazás futtatása              │
│                                                         │
│  Miért ez?: Nincs szükség szerver menedzsmentre,       │
│  automatikus skálázás, csak futó konténerért fizetsz   │
└─────────────────────────────────────────────────────────┘
```

**Konfiguráció:**
- **Task definíció**: 0.5 vCPU, 1 GB RAM
- **Service**: 2 példány (High Availability)
- **Cluster**: Logikai csoportosítás

---

#### **Container Registry (Image tárolás)**

```
┌─────────────────────────────────────────────────────────┐
│  ECR (Elastic Container Registry)                      │
│  ─────────────────────────────────────────────────────  │
│  Típus: Managed Service                                │
│  Költség: Tárhely GB/hónap + adatátvitel              │
│  Használat: Docker image-ek tárolása                   │
│                                                         │
│  Funkciók:                                             │
│  ✓ Automatikus sebezhetőség scan                       │
│  ✓ Image lifecycle policy (régi image-ek törlése)     │
│  ✓ Titkosítás (encryption at rest)                     │
│  ✓ IAM integráció (jogosultság kezelés)               │
└─────────────────────────────────────────────────────────┘
```

---

#### **Networking (Hálózat)**

```
┌─────────────────────────────────────────────────────────┐
│  VPC (Virtual Private Cloud)                           │
│  ─────────────────────────────────────────────────────  │
│  Típus: IaaS                                           │
│  Költség: Ingyenes (NAT Gateway, VPN díjköteles)      │
│  Használat: Izolált hálózati környezet                 │
│                                                         │
│  Komponensek ebben a projektben:                       │
│  ├── CIDR: 10.0.0.0/16 (65,536 IP cím)               │
│  ├── Public Subnet 1: 10.0.1.0/24 (AZ-1)             │
│  ├── Public Subnet 2: 10.0.2.0/24 (AZ-2)             │
│  ├── Internet Gateway: Külső internet elérés          │
│  ├── Route Tables: Forgalom irányítás                 │
│  └── Security Groups: Virtuális tűzfalak              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ALB (Application Load Balancer)                       │
│  ─────────────────────────────────────────────────────  │
│  Típus: Managed Service                                │
│  Költség: Óradíj + feldolgozott GB                     │
│  Használat: HTTP/HTTPS forgalom elosztása             │
│                                                         │
│  Funkciók:                                             │
│  ✓ Health check (egészséges példányok ellenőrzése)    │
│  ✓ Auto scaling integráció                            │
│  ✓ SSL/TLS termination                                 │
│  ✓ Path-based routing (URL alapú irányítás)           │
│  ✓ Multi-AZ (magas rendelkezésre állás)               │
└─────────────────────────────────────────────────────────┘
```

---

#### **Storage (Tárolás)**

```
┌─────────────────────────────────────────────────────────┐
│  S3 (Simple Storage Service)                           │
│  ─────────────────────────────────────────────────────  │
│  Típus: Object Storage (PaaS)                          │
│  Költség: GB/hónap + API kérések                       │
│  Használat: Terraform state fájl tárolása              │
│                                                         │
│  Tulajdonságok:                                        │
│  ✓ 99.999999999% (11 nines) durability                │
│  ✓ Versioning (verziókezelés)                          │
│  ✓ Encryption at rest (AES-256)                        │
│  ✓ Access control (bucket policies, ACL)              │
│  ✓ Lifecycle policies (automatikus archíválás)        │
└─────────────────────────────────────────────────────────┘
```

---

#### **Database (Adatbázis)**

```
┌─────────────────────────────────────────────────────────┐
│  DynamoDB                                               │
│  ─────────────────────────────────────────────────────  │
│  Típus: NoSQL Database (Serverless)                    │
│  Költség: Olvasás/írás egységek vagy on-demand        │
│  Használat: Terraform state locking                    │
│                                                         │
│  Funkciók ebben a projektben:                         │
│  ✓ Atomi lock műveletek (versenyhelyzet elkerülése)   │
│  ✓ Consistent reads (konzisztens olvasás)             │
│  ✓ Low latency (< 10ms válaszidő)                     │
│                                                         │
│  Struktúra:                                            │
│  ┌──────────────┬──────────────┬──────────────┐       │
│  │ LockID (PK)  │ Info         │ Timestamp    │       │
│  ├──────────────┼──────────────┼──────────────┤       │
│  │ state-file   │ user@host    │ 2026-01-22   │       │
│  └──────────────┴──────────────┴──────────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

#### **Monitoring & Logging**

```
┌─────────────────────────────────────────────────────────┐
│  CloudWatch                                             │
│  ─────────────────────────────────────────────────────  │
│  Típus: Managed Monitoring Service                     │
│  Költség: Ingested GB + tárolás + metrikák             │
│  Használat: Konténer logok és metrikák                 │
│                                                         │
│  Komponensek:                                          │
│  ├── Log Groups: Logok szervezése                     │
│  │   ├── /ecs/ai-agent-tutorial/app                   │
│  │   ├── /ecs/ai-agent-tutorial/prometheus            │
│  │   └── /ecs/ai-agent-tutorial/grafana               │
│  ├── Metrics: CPU, RAM, hálózat metrikák              │
│  ├── Alarms: Riasztások threshold alapján             │
│  └── Container Insights: ECS specifikus metrikák       │
└─────────────────────────────────────────────────────────┘
```

---

#### **Security & Identity**

```
┌─────────────────────────────────────────────────────────┐
│  IAM (Identity and Access Management)                  │
│  ─────────────────────────────────────────────────────  │
│  Típus: Global Service (Ingyenes)                      │
│  Használat: Jogosultság kezelés                        │
│                                                         │
│  Ebben a projektben használt IAM komponensek:          │
│                                                         │
│  1. IAM Role: terraform-github-deployer                │
│     └── Trust Policy: GitHub Actions OIDC provider     │
│     └── Permissions: S3, DynamoDB, ECR, ECS, VPC      │
│                                                         │
│  2. IAM Role: ecs-task-execution-role                  │
│     └── Trust Policy: ECS szolgáltatás                 │
│     └── Permissions: ECR pull, CloudWatch write        │
│                                                         │
│  3. OIDC Provider: GitHub Actions                      │
│     └── Célja: Jelszó nélküli hitelesítés             │
│     └── Token exchange: GitHub JWT → AWS credentials  │
└─────────────────────────────────────────────────────────┘
```

---

### AWS Költségbecslés - Ez az Alkalmazás

**Havi költség breakdown (becslés):**

```
┌────────────────────────────┬──────────────┬─────────────┐
│ Szolgáltatás               │ Konfiguráció │ Becsült ár  │
├────────────────────────────┼──────────────┼─────────────┤
│ ECS Fargate                │ 0.5 vCPU     │             │
│ (2 task, 24/7)             │ 1 GB RAM     │ ~$25/hó     │
├────────────────────────────┼──────────────┼─────────────┤
│ Application Load Balancer  │ 1 ALB        │ ~$20/hó     │
│                            │ + 1GB adatát │             │
├────────────────────────────┼──────────────┼─────────────┤
│ ECR                        │ 5 GB tárhely │ ~$0.50/hó   │
├────────────────────────────┼──────────────┼─────────────┤
│ S3 (Terraform state)       │ < 1 GB       │ ~$0.02/hó   │
├────────────────────────────┼──────────────┼─────────────┤
│ DynamoDB (state lock)      │ On-demand    │ ~$0.01/hó   │
├────────────────────────────┼──────────────┼─────────────┤
│ CloudWatch Logs            │ 5 GB/hó      │ ~$2.50/hó   │
├────────────────────────────┼──────────────┼─────────────┤
│ VPC, Security Groups       │ Ingyenes     │ $0          │
├────────────────────────────┴──────────────┼─────────────┤
│ ÖSSZESEN (körülbelül):                    │ ~$48/hó     │
└───────────────────────────────────────────┴─────────────┘

💡 Megjegyzés: Ez egy alap konfiguráció. Production környezetben
   multi-AZ, backup, WAF, további monitoring növeli a költséget.
```

**Költségoptimalizálási tippek:**
- ✅ Fargate Spot: Akár 70% megtakarítás (nem kritikus terheléseknél)
- ✅ Savings Plans: 1 éves commitment → ~40% megtakarítás
- ✅ Auto-scaling: Éjszaka scale-down → 30-50% megtakarítás
- ✅ S3 Lifecycle: Régi log-ok Glacier-be → 80% tárhely megtakarítás
- ✅ CloudWatch Log retention: 7 nap helyett 3 nap → 50% log költség csökkenés

---

### AWS Globális Infrastruktúra

#### Regions (Régiók)

AWS datacenterek földrajzi csoportosítása:

```
🌍 Európa:
├── eu-central-1 (Frankfurt) ← Ezt használjuk!
├── eu-west-1 (Dublin)
├── eu-west-2 (London)
├── eu-north-1 (Stockholm)
└── eu-south-1 (Milan)

🇺🇸 USA:
├── us-east-1 (N. Virginia)
├── us-west-2 (Oregon)
└── ...

🌏 Ázsia-Csendes-óceáni:
├── ap-southeast-1 (Singapore)
└── ...
```

**Miért Frankfurt (eu-central-1)?**
- ✅ GDPR compliance (EU adatvédelem)
- ✅ Alacsony latency Európában
- ✅ Sok AWS szolgáltatás elérhető
- ✅ Versenyképes árazás

#### Availability Zones (AZ)

Egy régión belüli független datacenterek:

```
eu-central-1 régió
├── eu-central-1a (AZ-1) ← Public Subnet 1
├── eu-central-1b (AZ-2) ← Public Subnet 2
└── eu-central-1c (AZ-3)

Miért több AZ?
─────────────
Ha eu-central-1a kiesik (áramszünet, tűz, stb.):
→ eu-central-1b még fut
→ ALB automatikusan átirányítja a forgalmat
→ Alkalmazás továbbra is elérhető
→ 99.99% uptime SLA teljesíthető
```

---

### AWS Best Practices - Amit követünk ebben a projektben

#### 1. **Security (Biztonság)**
```
✅ IAM Roles használata (nem access key-k)
✅ OIDC authentication (jelszó nélküli)
✅ Security Groups (least privilege principle)
✅ Encryption at rest (S3, ECR)
✅ Encryption in transit (HTTPS/TLS)
✅ Private subnets használata (amikor lehetséges)
✅ No hardcoded secrets (environment variables)
```

#### 2. **Reliability (Megbízhatóság)**
```
✅ Multi-AZ deployment (2+ availability zone)
✅ Health checks (ALB + ECS)
✅ Auto-restart on failure
✅ Graceful shutdown (deregistration delay)
✅ Rolling deployment (zero-downtime)
```

#### 3. **Performance Efficiency (Teljesítmény)**
```
✅ Right-sizing (megfelelő instance méret)
✅ Auto-scaling (load alapú)
✅ CDN használata statikus tartalmakhoz (opcionális)
✅ Caching (application + ALB szinten)
```

#### 4. **Cost Optimization (Költség optimalizálás)**
```
✅ Fargate Spot instances
✅ ECR lifecycle policy (régi image-ek törlése)
✅ CloudWatch log retention (csak 7 nap)
✅ S3 lifecycle (log archíválás)
✅ Right-sizing (ne túl nagy instance-ok)
```

#### 5. **Operational Excellence (Működési kiválóság)**
```
✅ Infrastructure as Code (Terraform)
✅ CI/CD pipeline (GitHub Actions)
✅ Automated deployments
✅ Monitoring & logging (CloudWatch)
✅ Tagging strategy (költség követés)
```

---

## Bevezetés

Ez az útmutató egy modern DevOps deployment pipeline-t mutat be, amely egy AI agent alkalmazást telepít AWS cloud környezetbe. A pipeline automatizálja az infrastruktúra létrehozását, a konténer build folyamatot és a deployment-et.

### Mit fogunk tanulni?

- ☁️ Cloud infrastruktúra menedzsment (AWS)
- 🏗️ Infrastructure as Code (Terraform)
- 🔄 CI/CD pipeline (GitHub Actions)
- 🐳 Konténerizáció (Docker)
- 📊 Monitoring és Observability (Prometheus, Grafana)

---

## Technológiai Áttekintés

### 1. 🐳 Docker - Konténerizáció

#### Mi az a Docker?
A Docker egy platform, amely lehetővé teszi alkalmazások csomagolását konténerekbe. A konténerek könnyűsúlyú, hordozható egységek, amelyek tartalmazzák az alkalmazást és minden függőségét.

#### Miért használjuk?
- ✅ **Konzisztencia**: "Works on my machine" probléma megszűnése
- ✅ **Izoláció**: Minden alkalmazás saját környezetben fut
- ✅ **Hordozhatóság**: Ugyanaz a konténer fut lokálisan, teszten és production-ben
- ✅ **Skálázhatóság**: Könnyű több példányt indítani

#### Fő komponensek:
- **Dockerfile**: Recept a konténer image elkészítéséhez
- **Docker Image**: Végrehajtható csomag (mint egy template)
- **Docker Container**: Futó image példány
- **Docker Registry**: Image tárolás (pl. Docker Hub, AWS ECR)

---

### 2. ☁️ AWS (Amazon Web Services) - Cloud Platform

#### Mi az AWS?
Az Amazon felhőszolgáltatás platformja, amely számítási kapacitást, tárhelyet és számos más szolgáltatást biztosít.

#### Ebben a projektben használt AWS szolgáltatások:

##### **ECR (Elastic Container Registry)**
- **Célja**: Docker image-ek tárolása
- **Analógia**: Mint egy privát Docker Hub
- **Funkciók**: 
  - Image verziózás
  - Automatikus sebezhetőség scan
  - Titkosított tárolás

##### **ECS (Elastic Container Service)**
- **Célja**: Konténerek futtatása és menedzsmentje
- **Komponensek**:
  - **Cluster**: Konténerek logikai csoportja
  - **Service**: Konténer példányok menedzsmentje
  - **Task Definition**: Konténer konfigurációs sablon
  - **Fargate**: Szerver nélküli konténer futtatás (nem kell EC2 instance-okat menedzselni)

##### **VPC (Virtual Private Cloud)**
- **Célja**: Izolált hálózati környezet
- **Komponensek**:
  - **Subnets**: Hálózat szegmentálása (public/private)
  - **Internet Gateway**: Külső internet elérés
  - **NAT Gateway**: Privát subnet-ek internet elérése
  - **Route Tables**: Forgalom irányítás
  - **Security Groups**: Virtuális tűzfalak

##### **ALB (Application Load Balancer)**
- **Célja**: Forgalom elosztása konténerek között
- **Funkciók**:
  - Health check
  - Auto scaling integráció
  - SSL/TLS támogatás
  - Path-based routing

##### **S3 (Simple Storage Service)**
- **Célja**: Fájlok és objektumok tárolása
- **Használat ebben a projektben**: Terraform state fájlok tárolása

##### **DynamoDB**
- **Célja**: NoSQL adatbázis
- **Használat ebben a projektben**: Terraform state locking (párhuzamos futások elkerülése)

##### **CloudWatch**
- **Célja**: Monitorozás és logging
- **Funkciók**:
  - Konténer logok gyűjtése
  - Metrikák tárolása
  - Riasztások

##### **IAM (Identity and Access Management)**
- **Célja**: Jogosultság kezelés
- **Komponensek**:
  - **Roles**: Átmeneti jogosultságok
  - **Policies**: Engedélyek definiálása
  - **OIDC Provider**: GitHub Actions integráció (jelszó nélküli hitelesítés)

---

### 3. 🏗️ Terraform - Infrastructure as Code (IaC)

#### Mi az a Terraform?
Egy nyílt forráskódú eszköz, amely lehetővé teszi az infrastruktúra kódként történő definiálását, verziókezelését és automatikus létrehozását.

#### Miért használjuk?
- ✅ **Verziókezelés**: Infrastruktúra változások nyomon követése Git-tel
- ✅ **Reprodukálhatóság**: Ugyanaz az infrastruktúra bármikor újra létrehozható
- ✅ **Dokumentáció**: A kód dokumentálja az infrastruktúrát
- ✅ **Multi-cloud**: Ugyanaz az eszköz működik AWS, GCP, Azure-on
- ✅ **Plan & Apply**: Változások előnézete alkalmazás előtt

#### Terraform architektúra:

```
┌─────────────────────────────────────────┐
│         Terraform CLI                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      Configuration Files (.tf)          │
│  - provider.tf (AWS kapcsolat)          │
│  - main.tf (erőforrások)                │
│  - variables.tf (változók)              │
│  - backend.tf (state tárolás)           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│         Terraform State                 │
│  (terraform.tfstate)                    │
│  Tárolja az aktuális infrastruktúra     │
│  állapotát - S3-ban tárolva             │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│         Cloud Provider (AWS)            │
│  Tényleges erőforrások létrehozása      │
└─────────────────────────────────────────┘
```

#### Fő Terraform parancsok:
- `terraform init`: Provider letöltése, backend inicializálás
- `terraform plan`: Változások előnézete
- `terraform apply`: Változások alkalmazása
- `terraform destroy`: Infrastruktúra törlése
- `terraform state`: State fájl menedzsment

---

### 4. 🔄 GitHub Actions - CI/CD Pipeline

#### Mi az a CI/CD?
- **CI (Continuous Integration)**: Kód folyamatos integrálása, tesztelése
- **CD (Continuous Deployment)**: Automatikus telepítés production környezetbe

#### Mi az a GitHub Actions?
GitHub beépített automatizációs platform, amely lehetővé teszi workflow-k létrehozását kód változásokra reagálva.

#### GitHub Actions architektúra:

```
┌───────────────────────────────────────────────┐
│         GitHub Repository                     │
│  (kód, .github/workflows/deploy.yml)          │
└────────────┬──────────────────────────────────┘
             │ Push to main branch
             ▼
┌───────────────────────────────────────────────┐
│         GitHub Actions Runner                 │
│  (Ubuntu VM a GitHub infrastruktúrán)         │
│                                               │
│  ┌─────────────────────────────────────┐     │
│  │  Job 1: bootstrap-state             │     │
│  │  - Terraform state backend setup    │     │
│  └─────────────────────────────────────┘     │
│                                               │
│  ┌─────────────────────────────────────┐     │
│  │  Job 2: build-and-deploy            │     │
│  │  - Checkout code                    │     │
│  │  - Configure AWS credentials        │     │
│  │  - Build Docker image               │     │
│  │  - Push to ECR                      │     │
│  │  - Run Terraform                    │     │
│  │  - Deploy to ECS                    │     │
│  └─────────────────────────────────────┘     │
└────────────┬──────────────────────────────────┘
             │
             ▼
┌───────────────────────────────────────────────┐
│              AWS Cloud                        │
│  - ECR: Docker image                          │
│  - ECS: Futó konténerek                       │
└───────────────────────────────────────────────┘
```

#### Workflow komponensek:
- **Trigger**: Mi indítja el a pipeline-t (pl. push, pull request)
- **Jobs**: Munkák, amelyek futnak
- **Steps**: Lépések egy job-on belül
- **Actions**: Újrafelhasználható komponensek (pl. checkout, AWS login)

---

### 5. 📊 Monitoring Stack

#### Prometheus - Metrikák gyűjtése
- **Célja**: Time-series adatbázis metrikák tárolására
- **Pull-based**: Periodikusan lekéri a metrikákat az alkalmazásoktól
- **PromQL**: Saját lekérdező nyelv

#### Grafana - Vizualizáció
- **Célja**: Metrikák megjelenítése dashboardokon
- **Data Source**: Prometheushoz kapcsolódik
- **Riasztások**: Alert-ek konfigurálása

---

## Kódminták és Konfiguráció

### 1. 🐳 Docker Konfiguráció

#### Dockerfile

Ez a fájl definiálja, hogyan építsük fel az alkalmazás image-ét.

```dockerfile
# Alap image kiválasztása - Python 3.11 slim verzió (kisebb méret)
FROM python:3.11-slim

# Munkakönyvtár beállítása a konténerben
WORKDIR /app

# Függőségek fájl másolása és telepítése
# Ezt külön lépésben csináljuk a Docker layer caching miatt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Alkalmazás kód másolása
COPY app/ ./app/
COPY prompts/ ./prompts/

# Biztonsági best practice: non-root user létrehozása
# Soha ne futtassunk konténert root userként!
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Port publikálása (dokumentációs célból)
EXPOSE 8000

# Alkalmazás indítása
# uvicorn: Python ASGI szerver
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Fontos koncepciók:**
- **Layer caching**: Docker cacheli a lépéseket, csak a változott részeket buildeli újra
- **Multi-stage build**: (Itt nincs használva, de production-ben gyakori)
- **Security**: Non-root user használata kötelező!

---

#### docker-compose.yml

Helyi fejlesztéshez és teszteléshez használjuk. Több konténert tud összehangolni.

```yaml
version: '3.8'

services:
  # Fő alkalmazás
  agent-demo:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: agent-demo
    ports:
      - "8000:8000"  # HOST:CONTAINER port mapping
    env_file:
      - .env  # Környezeti változók fájlból
    networks:
      - monitoring  # Megosztott hálózat más szolgáltatásokkal
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Prometheus metrika gyűjtő
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    networks:
      - monitoring

  # Grafana dashboard
  grafana:
    image: grafana/grafana:10.2.2
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_AUTH_ANONYMOUS_ENABLED=true
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge
```

**Kulcsfogalmak:**
- **Services**: Független konténerek
- **Networks**: Konténerek közötti kommunikáció
- **Volumes**: Adatok perzisztálása és konfigurációk megosztása
- **Health checks**: Konténer állapot ellenőrzés

---

### 2. 🏗️ Terraform Konfiguráció

#### provider.tf - AWS Provider beállítása

```hcl
# Terraform verzió és provider követelmények
terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"  # 5.x verzió, minor és patch frissítések engedélyezve
    }
  }
}

# AWS Provider konfiguráció
provider "aws" {
  region = var.aws_region  # Változóból jön (pl. eu-central-1)

  # Automatikus taggek minden erőforrásra
  default_tags {
    tags = {
      Environment = var.environment  # pl. "production"
      ManagedBy   = "Terraform"      # Jelzi, hogy Terraform kezeli
      Project     = var.project_name  # Projekt név
    }
  }
}
```

**Miért fontos a tagging?**
- Költségkövetés projektenként
- Erőforrások könnyebb megtalálása
- Automatizált cleanup
- Compliance és audit

---

#### backend.tf - Terraform State tárolás

```hcl
# Remote backend konfiguráció - S3 + DynamoDB
terraform {
  backend "s3" {
    bucket         = "terraform-state-021580456215-ai-agent-infra"
    key            = "ai-agent-tutorial/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true  # State file titkosítása
    dynamodb_table = "terraform-state-lock"  # Párhuzamos futás megakadályozása
  }
}
```

**Miért nem lokális state?**
- ❌ Lokális state: Csak egy dev gépen van, nincs verziókezelve, nem látható másoknak
- ✅ Remote state: Megosztott, verziókezelt, lockolt, biztonságos

**State locking működése:**
1. Terraform megpróbál írni a DynamoDB táblába
2. Ha sikerül → kap egy lock-ot, folytathatja
3. Ha nem sikerül (más már lock-olta) → vár vagy hibát dob
4. Munka végén feloldja a lock-ot

---

#### ecr.tf - Docker Registry

```hcl
# ECR Repository a Docker image-eknek
resource "aws_ecr_repository" "app" {
  name                 = var.ecr_repository_name  # pl. "ai-agent-app"
  image_tag_mutability = "MUTABLE"  # Tag-ek felülírhatóak

  # Automatikus sebezhetőség vizsgálat minden push-nál
  image_scanning_configuration {
    scan_on_push = true
  }

  # Titkosítás rest-ben
  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name = "${var.project_name}-ecr-repository"
  }
}

# Lifecycle policy - régi image-ek törlése
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Utolsó 10 image megtartása"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v"]
          countType     = "imageCountMoreThan"
          countNumber   = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Tag nélküli image-ek törlése 7 nap után"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = 7
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
```

**Lifecycle Policy miért fontos?**
- ECR tárolás költséggel jár
- Régi, nem használt image-ek foglalják a helyet
- Automatikus cleanup → költség csökkentés

---

#### vpc.tf - Hálózati infrastruktúra

```hcl
# VPC létrehozása - saját izolált hálózat
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr  # pl. "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway - VPC internet elérése
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnet 1 - első availability zone
resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_1_cidr  # pl. "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true  # Automatikus public IP

  tags = {
    Name = "${var.project_name}-public-subnet-1"
    Type = "public"
  }
}

# Public Subnet 2 - második availability zone (HA miatt)
resource "aws_subnet" "public_2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_2_cidr  # pl. "10.0.2.0/24"
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-2"
    Type = "public"
  }
}

# Route Table a public subnet-eknek
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  # Default route az internet felé
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# Route table asszociáció
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

# Security Group az ALB-nek
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  # Bejövő HTTP forgalom mindenhonnan
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP from anywhere"
  }

  # Bejövő HTTPS forgalom (ha van SSL)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS from anywhere"
  }

  # Kimenő forgalom mindenhova
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"  # minden protokoll
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# Security Group az ECS task-oknak
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-tasks-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id

  # Bejövő forgalom csak az ALB-től
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "Allow traffic from ALB"
  }

  # Kimenő forgalom mindenhova (pl. ECR pull, internet API-k)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "${var.project_name}-ecs-tasks-sg"
  }
}
```

**Hálózati architektúra magyarázat:**

```
┌─────────────────── VPC (10.0.0.0/16) ───────────────────┐
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │          Internet Gateway                        │   │
│  └────────────┬─────────────────────────────────────┘   │
│               │                                          │
│               ▼                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │    Application Load Balancer (ALB)               │   │
│  │    Public IP, Security Group: HTTP/HTTPS         │   │
│  └────────────┬─────────────────────────────────────┘   │
│               │                                          │
│       ┌───────┴────────┐                                │
│       ▼                ▼                                 │
│  ┌─────────────┐  ┌─────────────┐                       │
│  │ Public      │  │ Public      │                       │
│  │ Subnet 1    │  │ Subnet 2    │                       │
│  │ AZ: eu-c-1a │  │ AZ: eu-c-1b │                       │
│  │ 10.0.1.0/24 │  │ 10.0.2.0/24 │                       │
│  │             │  │             │                       │
│  │ ┌─────────┐ │  │ ┌─────────┐ │                       │
│  │ │ECS Task │ │  │ │ECS Task │ │                       │
│  │ │(Fargate)│ │  │ │(Fargate)│ │                       │
│  │ └─────────┘ │  │ └─────────┘ │                       │
│  └─────────────┘  └─────────────┘                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**Availability Zones miért fontosak?**
- Ha egy datacenter kiesik, a másik még fut
- Load balancer automatikusan átirányítja a forgalmat
- AWS best practice: minimum 2 AZ

---

#### ecs.tf - Konténer orchestration

```hcl
# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  # Container Insights engedélyezése (részletes metrikák)
  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-ecs-cluster"
  }
}

# CloudWatch Log Group az alkalmazásnak
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.project_name}/app"
  retention_in_days = 7  # Logok törlése 7 nap után (költség optimalizálás)

  tags = {
    Name = "${var.project_name}-app-logs"
  }
}

# IAM Role az ECS Task végrehajtásához
# Ez a role pull-olja az ECR image-et és írja a CloudWatch log-okat
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-ecs-task-execution-role"

  # Trust policy - ECS szolgáltatás használhatja ezt a role-t
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Managed policy csatolása (AWS által készített policy)
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Task Definition - konténer konfiguráció sablon
resource "aws_ecs_task_definition" "app" {
  family                   = "${var.project_name}-task"
  network_mode             = "awsvpc"  # Saját network interface minden tasknak
  requires_compatibilities = ["FARGATE"]  # Serverless konténerek
  cpu                      = "512"   # 0.5 vCPU
  memory                   = "1024"  # 1 GB RAM
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn

  # Konténer definíciók JSON-ben
  container_definitions = jsonencode([
    {
      name  = "app"
      image = "${aws_ecr_repository.app.repository_url}:latest"
      
      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      # Környezeti változók
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        },
        {
          name  = "LOG_LEVEL"
          value = "INFO"
        }
      ]

      # CloudWatch logging konfiguráció
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.app.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      # Health check
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/healthz || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-task-definition"
  }
}

# ECS Service - task példányok menedzsmentje
resource "aws_ecs_service" "app" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2  # 2 task példány (HA)
  launch_type     = "FARGATE"

  # Hálózati konfiguráció
  network_configuration {
    subnets          = [aws_subnet.public_1.id, aws_subnet.public_2.id]
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true  # Kell az ECR pull-hoz és internet API-khoz
  }

  # Load Balancer integráció
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 8000
  }

  # Deployment konfiguráció
  deployment_configuration {
    maximum_percent         = 200  # Deployment közben max 4 task futhat (2*200%)
    minimum_healthy_percent = 100  # Minimum 2 task fusson (2*100%)
  }

  # Várunk az ALB létrehozására
  depends_on = [aws_lb_listener.http]

  tags = {
    Name = "${var.project_name}-ecs-service"
  }
}
```

**ECS Deployment folyamat:**

```
1. Új task definition verzió
        ▼
2. ECS új task-okat indít (desired_count szerint)
        ▼
3. Új task-ok health check-je sikeres
        ▼
4. ALB elkezdi irányítani a forgalmat az új task-okra
        ▼
5. Régi task-ok leállítása (graceful shutdown)
        ▼
6. Deployment kész
```

---

#### alb.tf - Load Balancer

```hcl
# Application Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false  # Internet-facing
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]

  # Access log-ok S3-ba (opcionális, költséges)
  # access_logs {
  #   bucket  = aws_s3_bucket.lb_logs.id
  #   enabled = true
  # }

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# Target Group - ide irányítja az ALB a forgalmat
resource "aws_lb_target_group" "app" {
  name        = "${var.project_name}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"  # Fargate IP-based routing

  # Health check konfiguráció
  health_check {
    enabled             = true
    healthy_threshold   = 2    # 2 sikeres check után healthy
    interval            = 30   # 30 másodpercenként
    matcher             = "200"  # HTTP 200 OK válasz kell
    path                = "/healthz"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 3    # 3 sikertelen check után unhealthy
  }

  # Deregistration delay - mennyi ideig várjon az ALB a kapcsolatok lezárására
  deregistration_delay = 30

  tags = {
    Name = "${var.project_name}-target-group"
  }
}

# Listener - forgalom fogadása és továbbítása
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  # Default action - forgalom továbbítása a target group-ba
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
```

**Load Balancer működése:**

```
Internet
   │
   ▼
┌──────────────────┐
│   ALB Listener   │ :80
│   (HTTP)         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Target Group    │
│  Health Check    │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│Task 1  │ │Task 2  │
│Healthy │ │Healthy │
└────────┘ └────────┘
```

---

### 3. 🔄 GitHub Actions Pipeline

#### .github/workflows/deploy.yml

```yaml
name: Deploy AI Agent to AWS ECS

# Trigger konfiguráció
on:
  push:
    branches: [main]  # Automatikus deploy main branch-re push-nál
  workflow_dispatch:  # Manuális indítás is lehetséges

# Környezeti változók a teljes workflow-ra
env:
  AWS_REGION: eu-central-1
  ECR_REPOSITORY: ai-agent-app
  ECS_CLUSTER: ai-agent-tutorial-cluster
  ECS_SERVICE: ai-agent-tutorial-service
  TERRAFORM_DIR: terraform
  TERRAFORM_BOOTSTRAP_DIR: terraform-bootstrap

# OIDC authentication-höz kell
permissions:
  id-token: write  # AWS OIDC token kérése
  contents: read   # Repository kód olvasása

jobs:
  # Job 1: Terraform backend bootstrap (csak manuális futásnál)
  bootstrap-state:
    name: Bootstrap Terraform Remote State Backend
    runs-on: ubuntu-latest
    if: github.event_name == 'workflow_dispatch'  # Csak manual trigger-nél

    steps:
      # 1. Kód checkout
      - name: Checkout code
        uses: actions/checkout@v4

      # 2. AWS hitelesítés OIDC-vel (jelszó nélkül!)
      - name: Configure AWS Credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::021580456215:role/terraform-github-deployer
          aws-region: ${{ env.AWS_REGION }}

      # 3. Terraform telepítése
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      # 4. Terraform init
      - name: Terraform Init (Bootstrap)
        working-directory: ${{ env.TERRAFORM_BOOTSTRAP_DIR }}
        run: terraform init

      # 5. Terraform plan (előnézet)
      - name: Terraform Plan (Bootstrap)
        working-directory: ${{ env.TERRAFORM_BOOTSTRAP_DIR }}
        run: terraform plan

      # 6. Terraform apply (végrehajtás)
      - name: Terraform Apply (Bootstrap)
        working-directory: ${{ env.TERRAFORM_BOOTSTRAP_DIR }}
        run: terraform apply -auto-approve

      # 7. Összefoglaló
      - name: Bootstrap Complete
        run: |
          echo "✅ Remote state backend infrastructure created successfully!"
          echo "📦 S3 Bucket: terraform-state-021580456215-ai-agent-infra"
          echo "🔒 DynamoDB Table: terraform-state-lock"

  # Job 2: Build és Deploy
  build-and-deploy:
    name: Build & Deploy to AWS
    runs-on: ubuntu-latest
    needs: [bootstrap-state]
    # Fut, ha bootstrap sikeres VAGY skip-elve lett (nem manual trigger)
    if: always() && (needs.bootstrap-state.result == 'success' || needs.bootstrap-state.result == 'skipped')

    steps:
      # 1. Kód checkout
      - name: Checkout code
        uses: actions/checkout@v4

      # 2. AWS login OIDC-vel
      - name: Configure AWS Credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::021580456215:role/terraform-github-deployer
          aws-region: ${{ env.AWS_REGION }}

      # 3. Terraform setup
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      # 4. AWS identity ellenőrzés (debug)
      - name: Debug - Verify AWS Identity
        run: |
          echo "=== AWS Caller Identity ==="
          aws sts get-caller-identity

      # 5. ECR login - Docker push-hoz kell
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      # 6. Docker image build és push
      - name: Build, tag, and push image to Amazon ECR
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}  # Git commit hash mint image tag
        run: |
          # Docker build
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f docker/Dockerfile .
          
          # Latest tag is
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          
          # Push both tags
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
          
          echo "Image pushed: $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG"

      # 7. Terraform Init
      - name: Terraform Init
        working-directory: ${{ env.TERRAFORM_DIR }}
        run: terraform init

      # 8. Terraform Plan
      - name: Terraform Plan
        working-directory: ${{ env.TERRAFORM_DIR }}
        run: terraform plan -out=tfplan

      # 9. Terraform Apply
      - name: Terraform Apply
        working-directory: ${{ env.TERRAFORM_DIR }}
        run: terraform apply -auto-approve tfplan

      # 10. ALB URL kiírása
      - name: Get Load Balancer URL
        working-directory: ${{ env.TERRAFORM_DIR }}
        run: |
          echo "🚀 Deployment Complete!"
          echo "📍 Application URL:"
          terraform output -raw alb_dns_name

      # 11. Force ECS service update (új image deploy)
      - name: Force ECS Service Update
        run: |
          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service ${{ env.ECS_SERVICE }} \
            --force-new-deployment \
            --region ${{ env.AWS_REGION }}

      # 12. Deployment állapot figyelés
      - name: Wait for Service Stability
        run: |
          echo "⏳ Waiting for service to stabilize..."
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services ${{ env.ECS_SERVICE }} \
            --region ${{ env.AWS_REGION }}
          echo "✅ Service is stable and running!"

      # 13. Deployment summary
      - name: Deployment Summary
        run: |
          echo "╔════════════════════════════════════════╗"
          echo "║   🎉 DEPLOYMENT SUCCESSFUL 🎉         ║"
          echo "╚════════════════════════════════════════╝"
          echo ""
          echo "📦 Docker Image: ${{ steps.login-ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ github.sha }}"
          echo "🏗️  Infrastructure: Terraform managed"
          echo "🚀 ECS Cluster: ${{ env.ECS_CLUSTER }}"
          echo "⚙️  ECS Service: ${{ env.ECS_SERVICE }}"
          echo "🌍 Region: ${{ env.AWS_REGION }}"
```

**GitHub Actions OIDC Authentication előnyei:**

❌ **Régi módszer (Access Key):**
```yaml
- name: Configure AWS Credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
```
- Probléma: Access key-ket tárolni kell GitHub Secrets-ben
- Biztonsági kockázat: ha leak-el, teljes hozzáférés
- Lejáratok kezelése nehézkes

✅ **Új módszer (OIDC):**
```yaml
- name: Configure AWS Credentials via OIDC
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::021580456215:role/terraform-github-deployer
    aws-region: eu-central-1
```
- Nincs hosszú élettartamú credential
- GitHub token-t AWS-nek mutatja → ideiglenes credential
- Automatikus lejárat
- Jobb audit trail

---

## Platform Migrálás

### AWS → Google Cloud Platform (GCP)

#### 1. Szolgáltatás megfeleltetések

| AWS Szolgáltatás | GCP Alternatíva | Funkció |
|-----------------|-----------------|---------|
| **ECR** (Elastic Container Registry) | **GCR / Artifact Registry** | Docker image tárolás |
| **ECS** (Elastic Container Service) | **Cloud Run / GKE** | Konténer futtatás |
| **Fargate** | **Cloud Run** | Serverless konténerek |
| **VPC** | **VPC** | Virtual hálózat |
| **ALB** (Application Load Balancer) | **Cloud Load Balancing** | Load balancer |
| **S3** | **Cloud Storage** | Object storage |
| **DynamoDB** | **Firestore / Cloud Spanner** | NoSQL adatbázis |
| **CloudWatch** | **Cloud Logging / Monitoring** | Logging és monitoring |
| **IAM Roles** | **Service Accounts** | Jogosultság kezelés |

#### 2. Terraform Provider változtatások

**AWS provider.tf:**
```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}
```

**GCP provider.tf:**
```hcl
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = "my-project-id"
  region  = "europe-west3"  # Frankfurt
}
```

#### 3. Backend konfiguráció változtatások

**AWS backend.tf:**
```hcl
terraform {
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

**GCP backend.tf:**
```hcl
terraform {
  backend "gcs" {
    bucket = "terraform-state-bucket"
    prefix = "terraform/state"
  }
}
```

**Különbségek:**
- GCS nem használ külön locking mechanizmust (built-in)
- Nincs külön DynamoDB tábla szükséges

#### 4. Container Registry

**AWS ECR (ecr.tf):**
```hcl
resource "aws_ecr_repository" "app" {
  name = "ai-agent-app"
  
  image_scanning_configuration {
    scan_on_push = true
  }
}
```

**GCP Artifact Registry:**
```hcl
resource "google_artifact_registry_repository" "app" {
  location      = "europe-west3"
  repository_id = "ai-agent-app"
  format        = "DOCKER"
  
  # Automatikus vulnerability scanning
  # (külön API kell hozzá: Container Analysis API)
}
```

#### 5. Konténer futtatás

**AWS ECS Fargate (ecs.tf):**
```hcl
resource "aws_ecs_cluster" "main" {
  name = "ai-agent-cluster"
}

resource "aws_ecs_service" "app" {
  name            = "ai-agent-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 2
  launch_type     = "FARGATE"
}
```

**GCP Cloud Run:**
```hcl
resource "google_cloud_run_service" "app" {
  name     = "ai-agent-service"
  location = "europe-west3"

  template {
    spec {
      containers {
        image = "europe-west3-docker.pkg.dev/my-project/ai-agent-app/app:latest"
        
        ports {
          container_port = 8000
        }
        
        resources {
          limits = {
            cpu    = "1000m"  # 1 vCPU
            memory = "512Mi"  # 512 MB
          }
        }
      }
      
      # Auto-scaling
      container_concurrency = 80
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "1"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Public access engedélyezése
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.app.name
  location = google_cloud_run_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

**Főbb különbségek:**
- Cloud Run teljes serverless (nincs cluster koncepció)
- Auto-scaling beépített, nincs desired_count
- Egyszerűbb konfiguráció
- Költséghatékonyabb kis terhelésnél (scale to zero)

#### 6. Load Balancer

**AWS ALB (alb.tf):**
```hcl
resource "aws_lb" "main" {
  name               = "ai-agent-alb"
  load_balancer_type = "application"
  subnets            = [aws_subnet.public_1.id, aws_subnet.public_2.id]
}

resource "aws_lb_target_group" "app" {
  name     = "ai-agent-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
}
```

**GCP Cloud Load Balancing:**
```hcl
# Cloud Run esetén nincs szükség külön LB-re!
# Cloud Run automatikusan ad egy HTTPS endpoint-ot

# Ha GKE-t használnánk:
resource "google_compute_global_address" "app" {
  name = "ai-agent-ip"
}

resource "google_compute_backend_service" "app" {
  name          = "ai-agent-backend"
  health_checks = [google_compute_health_check.app.id]
  
  backend {
    group = google_compute_instance_group.app.id
  }
}
```

#### 7. Hálózat (VPC)

**AWS VPC (vpc.tf):**
```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public_1" {
  vpc_id     = aws_vpc.main.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}
```

**GCP VPC:**
```hcl
resource "google_compute_network" "main" {
  name                    = "ai-agent-network"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "main" {
  name          = "ai-agent-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = "europe-west3"
  network       = google_compute_network.main.id
}

# Internet gateway automatikus GCP-ben
```

#### 8. GitHub Actions változtatások

**AWS deployment step:**
```yaml
- name: Configure AWS Credentials via OIDC
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::021580456215:role/terraform-github-deployer
    aws-region: eu-central-1

- name: Login to Amazon ECR
  uses: aws-actions/amazon-ecr-login@v2

- name: Push to ECR
  run: |
    docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```

**GCP deployment step:**
```yaml
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github'
    service_account: 'github-deployer@my-project.iam.gserviceaccount.com'

- name: Set up Cloud SDK
  uses: google-github-actions/setup-gcloud@v2

- name: Configure Docker for Artifact Registry
  run: gcloud auth configure-docker europe-west3-docker.pkg.dev

- name: Push to Artifact Registry
  run: |
    docker build -t europe-west3-docker.pkg.dev/my-project/ai-agent-app/app:$IMAGE_TAG .
    docker push europe-west3-docker.pkg.dev/my-project/ai-agent-app/app:$IMAGE_TAG

- name: Deploy to Cloud Run
  run: |
    gcloud run deploy ai-agent-service \
      --image europe-west3-docker.pkg.dev/my-project/ai-agent-app/app:$IMAGE_TAG \
      --platform managed \
      --region europe-west3 \
      --allow-unauthenticated
```

---

### GitHub Actions → Bitbucket Pipelines

#### 1. Fő különbségek

| Szempont | GitHub Actions | Bitbucket Pipelines |
|----------|---------------|---------------------|
| **Konfig fájl** | `.github/workflows/*.yml` | `bitbucket-pipelines.yml` |
| **Runner** | GitHub-hosted vagy self-hosted | Bitbucket-hosted vagy self-hosted |
| **Secrets** | Repository Secrets | Repository Variables (secured) |
| **Conditional execution** | `if:` kulcsszó | `step.condition` |
| **Artifacts** | `actions/upload-artifact` | Beépített artifacts |

#### 2. Konfiguráció konverzió

**GitHub Actions (.github/workflows/deploy.yml):**
```yaml
name: Deploy AI Agent to AWS ECS

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  AWS_REGION: eu-central-1
  ECR_REPOSITORY: ai-agent-app

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and Push
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
```

**Bitbucket Pipelines (bitbucket-pipelines.yml):**
```yaml
image: atlassian/default-image:3

definitions:
  steps:
    - step: &build-and-deploy
        name: Build and Deploy to AWS ECS
        services:
          - docker
        script:
          # AWS CLI telepítése
          - apt-get update && apt-get install -y awscli

          # AWS credentials beállítása
          - export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
          - export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
          - export AWS_DEFAULT_REGION=$AWS_REGION

          # ECR login
          - aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

          # Docker build és push
          - export IMAGE_TAG=$BITBUCKET_COMMIT
          - docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f docker/Dockerfile .
          - docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

          # Terraform
          - wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
          - unzip terraform_1.6.0_linux_amd64.zip
          - mv terraform /usr/local/bin/
          - cd terraform
          - terraform init
          - terraform plan
          - terraform apply -auto-approve

pipelines:
  branches:
    main:
      - step: *build-and-deploy
  
  custom:
    manual-deploy:
      - step: *build-and-deploy
```

#### 3. Secrets kezelés

**GitHub Actions:**
- Settings → Secrets and variables → Actions
- Repository secrets, Environment secrets, Organization secrets
- Használat: `${{ secrets.SECRET_NAME }}`

**Bitbucket Pipelines:**
- Repository settings → Pipelines → Repository variables
- Secured variables (masked in logs)
- Használat: `$VARIABLE_NAME`

#### 4. Conditional execution

**GitHub Actions:**
```yaml
jobs:
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
```

**Bitbucket Pipelines:**
```yaml
pipelines:
  branches:
    main:
      - step:
          name: Deploy
          deployment: production
          trigger: manual  # vagy automatic
```

#### 5. Artifacts és caching

**GitHub Actions:**
```yaml
- name: Upload artifact
  uses: actions/upload-artifact@v3
  with:
    name: build-artifact
    path: ./build

- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

**Bitbucket Pipelines:**
```yaml
definitions:
  caches:
    pip: ~/.cache/pip

pipelines:
  default:
    - step:
        name: Build
        caches:
          - pip
        script:
          - pip install -r requirements.txt
          - python build.py
        artifacts:
          - build/**
```

#### 6. Parallel execution

**GitHub Actions:**
```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
```

**Bitbucket Pipelines:**
```yaml
pipelines:
  default:
    - parallel:
        - step:
            name: Test Python 3.9
            image: python:3.9
            script:
              - pytest
        - step:
            name: Test Python 3.10
            image: python:3.10
            script:
              - pytest
        - step:
            name: Test Python 3.11
            image: python:3.11
            script:
              - pytest
```

---

### GitHub Actions → GitLab CI/CD

#### Konfiguráció konverzió

**GitHub Actions (.github/workflows/deploy.yml):**
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./deploy.sh
```

**GitLab CI/CD (.gitlab-ci.yml):**
```yaml
stages:
  - deploy

deploy:
  stage: deploy
  image: ubuntu:latest
  script:
    - ./deploy.sh
  only:
    - main
```

**Főbb különbségek:**
- GitLab CI/CD: `stages` és `stage` koncepció
- GitLab: `only/except` branch filtering
- GitLab: `image` közvetlenül a job-ban
- GitLab: Beépített Docker registry minden projekthez

---

## Gyakorlati Feladatok

### Feladat 1: Lokális Docker környezet

**Cél**: Docker és docker-compose használatának gyakorlása

1. Klónozd a repositoryt
2. Hozz létre `.env` fájlt az `OPENAI_API_KEY` környezeti változóval
3. Indítsd el a stack-et: `docker-compose up -d`
4. Ellenőrizd, hogy fut: `docker ps`
5. Nézd meg a logokat: `docker logs agent-demo`
6. Nyisd meg böngészőben:
   - Alkalmazás: http://localhost:8000
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000

**Kérdések:**
- Hány konténer fut?
- Mi a különbség a `docker-compose up` és `docker-compose up -d` között?
- Hogyan állíthatod le az összes konténert?

---

### Feladat 2: Terraform alapok

**Cél**: Terraform state és basic commands megértése

1. Navigálj a `terraform/` mappába
2. Futtatsd: `terraform init`
3. Futtatsd: `terraform plan`
4. Vizsgáld meg a kimenetet

**Kérdések:**
- Mit csinál a `terraform init`?
- Mire jó a `terraform plan`?
- Hol található a state fájl?
- Mi a különbség `terraform plan` és `terraform apply` között?

---

### Feladat 3: AWS infrastruktúra módosítás

**Cél**: Terraform használata valós infrastruktúra módosításra

**Módosítás**: Változtasd meg az ECS task-ok számát 2-ről 3-ra

1. Nyisd meg a `terraform/ecs.tf` fájlt
2. Keresd meg: `desired_count = 2`
3. Módosítsd: `desired_count = 3`
4. Futtatsd: `terraform plan`
5. Vizsgáld meg a változásokat
6. Futtatsd: `terraform apply`

**Kérdések:**
- Mit mutat a plan output?
- Melyik erőforrást módosítja?
- Mennyi idő alatt áll be az új task?

---

### Feladat 4: GitHub Actions pipeline tesztelés

**Cél**: CI/CD pipeline működésének megértése

1. Fork-old a repositoryt
2. Állíts be AWS credentials-t (vagy használj GCP-t)
3. Push-olj egy változtatást a `main` branch-re
4. Kövesd a workflow futását a GitHub Actions tab-ban

**Kérdések:**
- Milyen lépéseket hajt végre a pipeline?
- Mennyi ideig tart az egész deployment?
- Hol találod a Docker image-t push után?
- Hogyan tudnád manuálisan indítani a workflow-t?

---

### Feladat 5: Platform migrálás terv

**Cél**: Önálló gondolkodás, dokumentáció készítés

**Feladat**: Készíts egy részletes migrációs tervet az AWS-ről Azure-ra való átálláshoz.

**Tartalmazza:**
1. Azure szolgáltatás megfeleltetések (pl. ECR → ACR)
2. Terraform provider változtatások
3. GitHub Actions workflow módosítások
4. Várható költség különbségek
5. Migrációs lépések időrendi sorrendben
6. Kockázatok és azok kezelése

**Formátum**: Markdown dokumentum, minimum 2 oldal

---

### Feladat 6: Monitoring dashboard

**Cél**: Grafana dashboard customizálás

1. Nyisd meg Grafana-t: http://localhost:3000
2. Navigálj a "AI Agent Dashboard"-ra
3. Add hozzá új panelt:
   - Metrika: `http_requests_total`
   - Vizualizáció: Idősoros grafikon
   - Cím: "HTTP Requests per Endpoint"
4. Mentsd el a módosított dashboard-ot
5. Exportáld JSON-ben

**Kérdések:**
- Milyen más metrikák vannak elérhető?
- Hogyan tudnál alert-et beállítani?
- Mi az a PromQL?

---

## Összefoglalás

### Mit tanultunk?

✅ **Docker**: Konténerizáció, image build, multi-container orchestration
✅ **AWS**: Cloud szolgáltatások (ECR, ECS, VPC, ALB, S3, IAM)
✅ **Terraform**: Infrastructure as Code, state management, provider használat
✅ **GitHub Actions**: CI/CD pipeline, automatizált deployment
✅ **Monitoring**: Prometheus metrikák, Grafana dashboards
✅ **Platform Migrálás**: AWS ↔ GCP, GitHub ↔ Bitbucket konverziók

### Következő lépések

1. **Költség optimalizálás**: Fargate spot instances, auto-scaling finomhangolás
2. **Security**: Secrets Manager, VPC endpoints, private subnets
3. **High Availability**: Multi-region deployment, disaster recovery
4. **Advanced CI/CD**: Feature flags, canary deployments, rollback strategies
5. **Kubernetes**: ECS-ről K8s-re migrálás (EKS, GKE, AKS)

### További tanulási források

- 📚 [Terraform Registry](https://registry.terraform.io/) - Provider dokumentáció
- 📚 [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- 📚 [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- 📚 [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- 📚 [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)

---

## Kapcsolat és támogatás

Ha kérdésed van, vagy segítségre van szükséged:
- 📧 Email: [support@example.com](mailto:support@example.com)
- 💬 Slack: #devops-help channel
- 📖 Wiki: [Internal DevOps Wiki](https://wiki.example.com)

**Készítette**: DevOps Team  
**Verzió**: 1.0  
**Utolsó frissítés**: 2026. január 22.

---

© 2026 AI Agent Infrastructure Tutorial - Minden jog fenntartva
