output "tfstate_bucket_name" {
  value       = aws_s3_bucket.tfstate.id
  description = "Nombre del bucket creado — úsalo como 'bucket' en el backend S3 de environments/dev"
}