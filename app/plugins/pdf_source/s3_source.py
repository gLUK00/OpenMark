"""S3-based PDF source plugin."""

import os
from typing import Optional

from app.plugins.base import PDFSourcePlugin


class S3SourcePlugin(PDFSourcePlugin):
    """PDF source plugin that retrieves documents from AWS S3 bucket."""
    
    def __init__(self, config: dict):
        """Initialize the S3 source plugin.
        
        Args:
            config: Plugin configuration with S3 settings:
                - bucket_name: Name of the S3 bucket (required)
                - aws_access_key_id: AWS access key (optional if using IAM roles)
                - aws_secret_access_key: AWS secret key (optional if using IAM roles)
                - aws_session_token: AWS session token (optional, for temporary credentials)
                - region_name: AWS region (default: 'us-east-1')
                - prefix: Key prefix for documents (optional, e.g., 'documents/')
                - endpoint_url: Custom S3 endpoint (optional, for S3-compatible services like MinIO)
                - use_ssl: Use SSL for connections (default: True)
                - verify_ssl: Verify SSL certificates (default: True)
        """
        super().__init__(config)
        self.bucket_name = config.get('bucket_name')
        if not self.bucket_name:
            raise ValueError("S3 plugin requires 'bucket_name' in configuration")
        
        self.aws_access_key_id = config.get('aws_access_key_id')
        self.aws_secret_access_key = config.get('aws_secret_access_key')
        self.aws_session_token = config.get('aws_session_token')
        self.region_name = config.get('region_name', 'us-east-1')
        self.prefix = config.get('prefix', '')
        self.endpoint_url = config.get('endpoint_url')
        self.use_ssl = config.get('use_ssl', True)
        self.verify_ssl = config.get('verify_ssl', True)
        
        # Initialize S3 client lazily
        self._s3_client = None
    
    @property
    def s3_client(self):
        """Get or create the S3 client (lazy initialization).
        
        Returns:
            boto3 S3 client
        """
        if self._s3_client is None:
            try:
                import boto3
                from botocore.config import Config as BotoConfig
            except ImportError:
                raise ImportError(
                    "boto3 is required for S3 PDF source plugin. "
                    "Install it with: pip install boto3"
                )
            
            # Build client configuration
            boto_config = BotoConfig(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'standard'}
            )
            
            # Build client kwargs
            client_kwargs = {
                'service_name': 's3',
                'region_name': self.region_name,
                'config': boto_config,
                'use_ssl': self.use_ssl,
                'verify': self.verify_ssl
            }
            
            # Add credentials if provided (otherwise use IAM role/environment)
            if self.aws_access_key_id and self.aws_secret_access_key:
                client_kwargs['aws_access_key_id'] = self.aws_access_key_id
                client_kwargs['aws_secret_access_key'] = self.aws_secret_access_key
                if self.aws_session_token:
                    client_kwargs['aws_session_token'] = self.aws_session_token
            
            # Add custom endpoint if provided (for MinIO, LocalStack, etc.)
            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            self._s3_client = boto3.client(**client_kwargs)
        
        return self._s3_client
    
    def _get_s3_key(self, document_id: str) -> str:
        """Build the S3 key for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Full S3 key including prefix
        """
        # Add .pdf extension if not present
        if not document_id.endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        
        # Combine prefix and document_id
        if self.prefix:
            # Remove trailing slash from prefix if present
            prefix = self.prefix.rstrip('/')
            return f"{prefix}/{document_id}"
        return document_id
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document from S3.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        try:
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 PDF source plugin. "
                "Install it with: pip install boto3"
            )
        
        s3_key = self._get_s3_key(document_id)
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read()
            
            # Verify it's a PDF
            content_type = response.get('ContentType', '')
            if 'pdf' in content_type.lower() or content[:4] == b'%PDF':
                return content
            else:
                print(f"Warning: Content-Type '{content_type}' may not be a PDF for {s3_key}")
                return content
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                print(f"Document not found in S3: {s3_key}")
            elif error_code == 'AccessDenied':
                print(f"Access denied to S3 object: {s3_key}")
            else:
                print(f"S3 error fetching document {s3_key}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching document {s3_key} from S3: {e}")
            return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists in S3.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 PDF source plugin. "
                "Install it with: pip install boto3"
            )
        
        s3_key = self._get_s3_key(document_id)
        
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ('404', 'NoSuchKey'):
                return False
            # Log other errors but return False
            print(f"S3 error checking document existence {s3_key}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error checking document existence {s3_key}: {e}")
            return False
    
    def list_documents(self, max_results: int = 100) -> list:
        """List available documents in the S3 bucket.
        
        Args:
            max_results: Maximum number of documents to return (default: 100)
            
        Returns:
            List of document IDs (without .pdf extension)
        """
        try:
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 PDF source plugin. "
                "Install it with: pip install boto3"
            )
        
        documents = []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            list_kwargs = {
                'Bucket': self.bucket_name,
                'MaxKeys': min(max_results, 1000)
            }
            
            if self.prefix:
                list_kwargs['Prefix'] = self.prefix
            
            for page in paginator.paginate(**list_kwargs):
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    # Only include PDF files
                    if key.lower().endswith('.pdf'):
                        # Remove prefix and .pdf extension
                        doc_id = key
                        if self.prefix:
                            doc_id = doc_id[len(self.prefix):].lstrip('/')
                        doc_id = doc_id[:-4]  # Remove .pdf
                        documents.append(doc_id)
                        
                        if len(documents) >= max_results:
                            break
                
                if len(documents) >= max_results:
                    break
            
            return documents
            
        except ClientError as e:
            print(f"S3 error listing documents: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error listing documents from S3: {e}")
            return []
    
    def get_document_metadata(self, document_id: str) -> Optional[dict]:
        """Get metadata for a document in S3.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Dict with document metadata, or None if not found
        """
        try:
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 PDF source plugin. "
                "Install it with: pip install boto3"
            )
        
        s3_key = self._get_s3_key(document_id)
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'document_id': document_id,
                's3_key': s3_key,
                'content_type': response.get('ContentType', 'application/pdf'),
                'content_length': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag', '').strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ('404', 'NoSuchKey'):
                return None
            print(f"S3 error getting document metadata {s3_key}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error getting document metadata {s3_key}: {e}")
            return None
