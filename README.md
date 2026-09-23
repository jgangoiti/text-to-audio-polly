# text-to-audio-polly

> ⚠️ **Demo language / Idioma de la demo:** The demo video below was recorded in Spanish, using Amazon Polly's "Lucia" voice. The pipeline itself is language-agnostic — see [Language Detection](#language-detection--detección-de-idioma).
>
> El vídeo de demostración está grabado en español, usando la voz "Lucía" de Amazon Polly. El pipeline en sí es independiente del idioma — ver [Detección de idioma](#language-detection--detección-de-idioma).

---

## English

### Overview

`text-to-audio-polly` is an event-driven, serverless pipeline that converts text files into natural-sounding speech. A user uploads a `.txt` file to an S3 bucket; this triggers a Lambda function that detects the text's language with **Amazon Comprehend**, synthesizes audio with **Amazon Polly** using a matching voice, stores the resulting MP3 in a destination S3 bucket, and notifies the user by email via **Amazon SNS**.

The project was built as a portfolio piece to demonstrate asynchronous, event-driven architecture and integration with AWS AI services, using Terraform organized into reusable modules rather than a single monolithic configuration.

### Architecture

```mermaid
flowchart LR
    A[User] -->|uploads .txt| B[(S3 - Input Bucket)]
    B -->|S3 Event Trigger| C[Lambda: TTS Handler]
    C -->|detect language| D[Amazon Comprehend]
    D -->|language code| C
    C -->|synthesize speech| E[Amazon Polly]
    E -->|audio stream| C
    C -->|store .mp3| F[(S3 - Output Bucket)]
    C -->|publish message| G[Amazon SNS]
    G -->|notify| H[Lambda: Notifier]
    H -->|email with link| A
```

**Flow:**
1. A `.txt` file is uploaded to the input S3 bucket.
2. The upload triggers the **TTS handler Lambda**.
3. The handler calls **Amazon Comprehend** to detect the dominant language of the text.
4. Based on the detected language (with a fallback to Spanish if confidence is low or the language isn't supported), the handler selects a matching **Polly** voice and synthesizes the audio.
5. The resulting MP3 is stored in the output S3 bucket.
6. An **SNS** message triggers the **notifier Lambda**, which emails the user a link to the generated audio file.

### Language Detection

The handler doesn't assume a fixed language. It uses Amazon Comprehend to detect the dominant language of each uploaded text, then picks an appropriate Polly voice for that language automatically. If Comprehend's confidence is too low, or the detected language isn't supported by Polly, the handler falls back to Spanish (voice: Lucia).

### Tech Stack

| Layer | Service |
|---|---|
| Storage | Amazon S3 (input & output buckets) |
| Compute | AWS Lambda (Python) |
| Language detection | Amazon Comprehend |
| Text-to-speech | Amazon Polly |
| Notifications | Amazon SNS |
| Infrastructure as Code | Terraform (modular: `modules/` + `environments/`) |
| State backend | S3 with native locking (no DynamoDB) |
| Identity | Least-privilege IAM (customer-managed policy) |
| Region | `eu-west-1` |

### Project Structure

```
text-to-audio-polly/
├── terraform/
│   ├── bootstrap/              # tfstate bucket + native S3 locking backend
│   ├── modules/
│   │   ├── storage/             # S3 buckets
│   │   ├── notifications/       # SNS topic + subscriptions
│   │   ├── tts-pipeline/        # TTS Lambda, permissions, triggers
│   │   └── notifier/            # Notifier Lambda
│   └── environments/
│       └── dev/
├── src/
│   ├── lambda_handler/
│   │   └── handler.py           # Comprehend + Polly logic
│   └── notifier_handler/
│       └── handler.py           # SNS → email notification
└── docs/
    └── iam-policy.json          # Least-privilege IAM policy (with placeholders)
```

### Deployment

```bash
# 1. Bootstrap the remote state backend (one-time)
cd terraform/bootstrap
terraform init
terraform apply

# 2. Deploy the environment
cd ../environments/dev
terraform init
terraform apply
```

> Requires an AWS account with credentials configured, and an IAM user/role with sufficient permissions (see `docs/iam-policy.json` for the least-privilege policy used in this project).

### Cost Estimate

Approximate costs assuming light, portfolio-level usage (a handful of short text files per day), all within the `eu-west-1` region. Actual costs will vary with usage volume and text length.

| Service | Pricing basis | Estimated monthly cost (light use) |
|---|---|---|
| S3 (storage + requests) | ~1 GB stored, low request volume | < $0.05 |
| Lambda (2 functions) | Well within the AWS Free Tier (1M requests/month) | $0.00 |
| Amazon Comprehend | ~$0.0001 per unit (100 chars) of text analyzed | < $0.10 for light use |
| Amazon Polly | Standard voices: $4.00 per 1M characters (Free Tier: 5M chars/month for 12 months) | $0.00–$1.00 |
| Amazon SNS | First 1,000 email notifications/month free | $0.00 |
| **Total (light use, within Free Tier)** | | **≈ $0.00 – $1.00 / month** |

> Note: this is an illustrative estimate, not a guarantee. Use the [AWS Pricing Calculator](https://calculator.aws) for a precise projection based on your expected volume.

### Roadmap

- [ ] CI/CD with GitHub Actions (`terraform plan` on PR, `terraform apply` on merge to `main`)
- [ ] Unit tests with `moto` for both Lambda handlers
- [ ] Demo GIF/video
- [ ] Configurable tfstate bucket name (no manual `.tf` edits required to deploy)

---

## Español

### Descripción general

`text-to-audio-polly` es un pipeline serverless y orientado a eventos que convierte archivos de texto en audio con voz natural. El usuario sube un archivo `.txt` a un bucket de S3; esto dispara una función Lambda que detecta el idioma del texto con **Amazon Comprehend**, sintetiza el audio con **Amazon Polly** usando una voz acorde a ese idioma, guarda el MP3 resultante en un bucket de S3 de destino, y notifica al usuario por correo mediante **Amazon SNS**.

El proyecto se construyó como pieza de portfolio para demostrar arquitecturas asíncronas y orientadas a eventos, e integración con servicios de IA de AWS, usando Terraform organizado en módulos reutilizables en lugar de una configuración monolítica.

### Arquitectura

Ver el diagrama en la sección en inglés más arriba (el flujo es idéntico).

**Flujo:**
1. Se sube un archivo `.txt` al bucket de entrada de S3.
2. La subida dispara la **Lambda del handler de TTS**.
3. El handler llama a **Amazon Comprehend** para detectar el idioma dominante del texto.
4. Según el idioma detectado (con fallback a español si la confianza es baja o el idioma no está soportado), el handler elige una voz de **Polly** acorde y sintetiza el audio.
5. El MP3 resultante se guarda en el bucket de salida de S3.
6. Un mensaje de **SNS** dispara la **Lambda notificadora**, que envía al usuario un correo con el enlace al audio generado.

### Detección de idioma

El handler no asume un idioma fijo. Usa Amazon Comprehend para detectar el idioma dominante de cada texto subido, y elige automáticamente una voz de Polly adecuada a ese idioma. Si la confianza de Comprehend es demasiado baja, o el idioma detectado no está soportado por Polly, el handler recurre a español (voz Lucia) como fallback.

### Stack tecnológico

Ver la tabla en la sección en inglés (idéntica).

### Estructura del proyecto

Ver el árbol de directorios en la sección en inglés (idéntico).

### Despliegue

```bash
# 1. Bootstrap del backend de estado remoto (una sola vez)
cd terraform/bootstrap
terraform init
terraform apply

# 2. Desplegar el entorno
cd ../environments/dev
terraform init
terraform apply
```

> Requiere una cuenta de AWS con credenciales configuradas, y un usuario/rol IAM con permisos suficientes (ver `docs/iam-policy.json` para la política de mínimo privilegio usada en este proyecto).

### Estimación de coste

Coste aproximado asumiendo un uso ligero, de nivel portfolio (unos pocos archivos de texto cortos al día), todo dentro de la región `eu-west-1`. El coste real variará según el volumen de uso y la longitud de los textos.

| Servicio | Base de precio | Coste mensual estimado (uso ligero) |
|---|---|---|
| S3 (almacenamiento + peticiones) | ~1 GB almacenado, pocas peticiones | < $0,05 |
| Lambda (2 funciones) | Dentro de la capa gratuita (1M peticiones/mes) | $0,00 |
| Amazon Comprehend | ~$0,0001 por unidad (100 caracteres) analizada | < $0,10 en uso ligero |
| Amazon Polly | Voces estándar: $4,00 por 1M de caracteres (capa gratuita: 5M caracteres/mes durante 12 meses) | $0,00–$1,00 |
| Amazon SNS | Primeras 1.000 notificaciones por email al mes, gratis | $0,00 |
| **Total (uso ligero, dentro de la capa gratuita)** | | **≈ $0,00 – $1,00 / mes** |

> Nota: esta es una estimación ilustrativa, no una garantía. Usa la [calculadora de precios de AWS](https://calculator.aws) para una proyección precisa según tu volumen esperado.

### Próximos pasos

- [ ] CI/CD con GitHub Actions (`terraform plan` en PR, `terraform apply` al fusionar a `main`)
- [ ] Tests unitarios con `moto` para ambos handlers de Lambda
- [ ] GIF/vídeo de la demo
- [ ] Nombre del bucket de tfstate configurable (sin necesidad de editar `.tf` manualmente para desplegar)
