import boto3
import logging
import os
import json
import time
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from pprint import pprint

# Set up logging
logging.basicConfig(format='[%(asctime)s] %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeBasePermissions:
    def __init__(self, region, account_id, kb_name, kb_role_name, embedding_model_arn, bucket_name):
        """
        Initialize the KnowledgeBasePermissions class with required AWS details.
        """
        self.region = region
        self.account_id = account_id
        self.kb_name = kb_name
        self.kb_role_name = kb_role_name
        self.embedding_model_arn = embedding_model_arn 

        # Initialize AWS clients
        self.iam_client = boto3.client('iam', region_name=region)

        # Creating default policy names
        self.kb_bedrock_allow_policy_name = f"bd-kb-bedrock-allow-{self.kb_name}"
        self.kb_aoss_allow_policy_name = f"bd-kb-aoss-allow-{self.kb_name}"
        self.kb_s3_allow_policy_name = f"bd-kb-s3-allow-{self.kb_name}"

        self.bucket_name = bucket_name

    def create_kb_role(self):
        """
        Creates an IAM role with the necessary permissions for Amazon Bedrock Knowledge Base.
        Returns the Role with appropriate accesses for creating and managing a Knowledge Base.
        """
        # Create IAM Role for the agent and attach IAM policies
        assume_role_policy_document = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }]
        }

        assume_role_policy_document_json = json.dumps(assume_role_policy_document)
        self.kb_role = self.iam_client.create_role(
            RoleName=self.kb_role_name,
            AssumeRolePolicyDocument=assume_role_policy_document_json
        )
        self.kb_role_arn = self.kb_role['Role']['Arn']

        # Pause to make sure role is created
        time.sleep(10)
            
        self.iam_client.attach_role_policy(
            RoleName=self.kb_role_name,
            PolicyArn=self.create_kb_bedrock_policy()
        )

        self.iam_client.attach_role_policy(
            RoleName=self.kb_role_name,
            PolicyArn=self.create_aoss_policy()
        )

        self.iam_client.attach_role_policy(
            RoleName=self.kb_role_name,
            PolicyArn=self.create_s3_policy()
        )
        return
    
    def create_kb_bedrock_policy(self):
        """
        Creates an IAM policy with permissions for Amazon Bedrock Knowledge Base.
        Returns the Policy with appropriate accesses for creating and managing a Knowledge Base.
        """
        bedrock_kb_allow_fm_model_policy_statement = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AmazonBedrockAgentBedrockFoundationModelPolicy",
                    "Effect": "Allow",
                    "Action": "bedrock:InvokeModel",
                    "Resource": [
                        self.embedding_model_arn
                    ]
                }
            ]
        }

        kb_bedrock_policy_json = json.dumps(bedrock_kb_allow_fm_model_policy_statement)

        kb_bedrock_policy = self.iam_client.create_policy(
            PolicyName=self.kb_bedrock_allow_policy_name,
            PolicyDocument=kb_bedrock_policy_json
        )
        self.kb_bedrock_policy = kb_bedrock_policy
        return kb_bedrock_policy['Policy']['Arn']
    
    def create_aoss_policy(self):
        """
        Creates an IAM policy with permissions for Amazon OpenSearch Service.
        Returns the Policy with appropriate accesses for creating and managing OSS services for a Knowledge Base.
        """
        bedrock_kb_allow_aoss_policy_statement = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "aoss:APIAccessAll",
                    "Resource": [
                        f"arn:aws:aoss:{self.region}:{self.account_id}:collection/*"
                    ]
                }
            ]
        }


        kb_aoss_policy_json = json.dumps(bedrock_kb_allow_aoss_policy_statement)

        kb_aoss_policy = self.iam_client.create_policy(
            PolicyName=self.kb_aoss_allow_policy_name,
            PolicyDocument=kb_aoss_policy_json
        )
        self.kb_aoss_policy = kb_aoss_policy
        return kb_aoss_policy['Policy']['Arn']
    
    def create_s3_policy(self):
        """
        Creates an IAM policy with permissions for Amazon S3 bucket.
        Returns the Policy with appropriate accesses for creating and managing s3 services for a Knowledge Base.
        """
        kb_s3_allow_policy_statement = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowKBAccessDocuments",
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{self.bucket_name}/*",
                        f"arn:aws:s3:::{self.bucket_name}"
                    ],
                    "Condition": {
                        "StringEquals": {
                            "aws:ResourceAccount": f"{self.account_id}"
                        }
                    }
                }
            ]
        }


        kb_s3_json = json.dumps(kb_s3_allow_policy_statement)
        kb_s3_policy = self.iam_client.create_policy(
            PolicyName=self.kb_s3_allow_policy_name,
            PolicyDocument=kb_s3_json
        )
        self.kb_s3_policy = kb_s3_policy
        return kb_s3_policy['Policy']['Arn']
    
class VectorStorePermissions(KnowledgeBasePermissions):
    """
    Class that creates permissions for the Vector Store, given a vector store name as ID.
    """
    def __init__(self, 
                 region, 
                 account_id, 
                 bucket_name, 
                 kb_name, 
                 embedding_model_arn, 
                 kb_role_name):
        """
        Initialize the KnowledgeBaseSetup class with required AWS details.
        """
        super().__init__(region, account_id, kb_name, kb_role_name, embedding_model_arn, bucket_name)
        self.region = region
        self.account_id = account_id
        self.bucket_name = bucket_name
        self.kb_name = kb_name
        self.embedding_model_arn = embedding_model_arn
        self.kb_role_name = kb_role_name

        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=region)
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.os_serverless_client = boto3.client('opensearchserverless')
        self.sts_client = boto3.client('sts')
        self.sts_caller_identity_arn = self.sts_client.get_caller_identity()['Arn']

        # Creating default policy names for kb (knowledge base) permissions
        self.kb_bedrock_allow_policy_name = f"bd-kb-bedrock-allow-{self.kb_name}"
        self.kb_aoss_allow_policy_name = f"bd-kb-aoss-allow-{self.kb_name}"
        self.kb_s3_allow_policy_name = f"bd-kb-s3-allow-{self.kb_name}"

        # Creating default vars for vector store creation
        self.kb_collection_name = f"bedrock-kb-collection-{self.kb_name}"

    def set_vs_permissions(self):
        """
        Sets permissions for the Vector Store (i.e., OpenSearch Service) and the S3 bucket.
        """
        self.create_vs_security_policy()
        self.create_vs_network_policy()
        self.create_vs_data_policy()
        return

    def create_vs_security_policy(self):
        """
        Creates a security policy for the Vector Store (i.e., OpenSearch Service)
        """
        security_policy_json = {
            "Rules": [
                {
                    "ResourceType": "collection",
                    "Resource":[
                        f"collection/{self.kb_collection_name}"
                    ]
                }
            ],
            "AWSOwnedKey": True
        }
        _ = self.os_serverless_client.create_security_policy(
            description='security policy of aoss collection',
            name=self.kb_collection_name,
            policy=json.dumps(security_policy_json),
            type='encryption'
        )
        return

    def create_vs_network_policy(self):
        """
        Creates a network policy for the Vector Store (i.e., OpenSearch Service)
        """
        network_policy_json = [
        {
            "Rules": [
            {
                "Resource": [
                f"collection/{self.kb_collection_name}"
                ],
                "ResourceType": "dashboard"
            },
            {
                "Resource": [
                f"collection/{self.kb_collection_name}"
                ],
                "ResourceType": "collection"
            }
            ],
            "AllowFromPublic": True
        }
        ]

        _ = self.os_serverless_client.create_security_policy(
            description='network policy of aoss collection',
            name=self.kb_collection_name,
            policy=json.dumps(network_policy_json),
            type='network'
        )
        return 
    
    def create_vs_data_policy(self):
        data_policy_json = [
        {
            "Rules": [
            {
                "Resource": [
                f"collection/{self.kb_collection_name}"
                ],
                "Permission": [
                "aoss:DescribeCollectionItems",
                "aoss:CreateCollectionItems",
                "aoss:UpdateCollectionItems",
                "aoss:DeleteCollectionItems"
                ],
                "ResourceType": "collection"
            },
            {
                "Resource": [
                f"index/{self.kb_collection_name}/*"
                ],
                "Permission": [
                    "aoss:CreateIndex",
                    "aoss:DeleteIndex",
                    "aoss:UpdateIndex",
                    "aoss:DescribeIndex",
                    "aoss:ReadDocument",
                    "aoss:WriteDocument"
                ],
                "ResourceType": "index"
            }
            ],
            "Principal": [
                self.kb_role_arn,
                f"arn:aws:sts::{self.account_id}:assumed-role/Admin/*",
                self.sts_caller_identity_arn
            ],
            "Description": ""
        }
        ]

        _ = self.os_serverless_client.create_access_policy(
            description='data access policy for aoss collection',
            name=self.kb_collection_name,
            policy=json.dumps(data_policy_json),
            type='data'
        )
        return

class VectorStoreSetup(VectorStorePermissions):
    """
    Setup class for the Vector Store (OpenSearch Service + s3 connection) for the Knowledge Base.
    """
    def __init__(self,
                region,
                account_id,
                bucket_name,
                kb_name,
                embedding_model_arn,
                kb_role_name):
        """
        Initialize the VectorStoreSetup class with required AWS details.
        """
        super().__init__(region, account_id, bucket_name, kb_name, embedding_model_arn, kb_role_name)
        self.kb_metadataField = 'bedrock-knowledge-base-metadata'
        self.kb_textField = 'bedrock-knowledge-base-text'
        self.kb_vectorField = 'bedrock-knowledge-base-vector'
        self.kb_vector_index_name = "bedrock-knowledge-base-index"
        self.os_final_host = None # this is set by create_os_collection()

    def create_vs(self):
        """
        Creates the Vector Store (OpenSearch Service) for the Knowledge Base.
        """
        self.create_os_collection()
        self.create_os_search_index()
        return

    def create_os_collection(self):
        """
        Creates an OpenSearch Service collection for the Vector Store.
        """
        self.os_collection_response = self.os_serverless_client.create_collection(
            description='OpenSearch collection for Amazon Bedrock Knowledge Base',
            name=self.kb_collection_name,
            standbyReplicas='DISABLED',
            type='VECTORSEARCH'
        )
        # We set the collection arn to be re-used when we finally create the bedrock knowledge base
        self.collection_arn = self.os_collection_response["createCollectionDetail"]["arn"]

        # wait for collection creation
        response = self.os_serverless_client.batch_get_collection(names=[self.kb_collection_name])
        # Periodically check collection status
        while (response['collectionDetails'][0]['status']) == 'CREATING':
            print('Creating collection...')
            time.sleep(30)
            response = self.os_serverless_client.batch_get_collection(names=[self.kb_collection_name])
        print('\nCollection successfully created:')
        print(response["collectionDetails"])
        # Extract the collection endpoint from the response
        host = (response['collectionDetails'][0]['collectionEndpoint'])
        self.os_final_host = host.replace("https://", "")
        return 
    
    def create_os_search_index(self):
        credentials = boto3.Session().get_credentials()
        service = 'aoss'
        awsauth = AWS4Auth(
            credentials.access_key, 
            credentials.secret_key,
            self.region, 
            service, 
            session_token=credentials.token
        )

        # Build the OpenSearch client
        open_search_client = OpenSearch(
            hosts=[{'host': self.os_final_host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )
        # It can take up to a minute for data access rules to be enforced
        time.sleep(45)
        index_body = {
            "settings": {
                "index.knn": True,
                "number_of_shards": 1,
                "knn.algo_param.ef_search": 512,
                "number_of_replicas": 0,
            },
            "mappings": {
                "properties": {}
            }
        }

        index_body["mappings"]["properties"][self.kb_vectorField] = {
            "type": "knn_vector",
            "dimension": 1536,
            "method": {
                "name": "hnsw",
                "engine": "faiss"
            },
        }

        index_body["mappings"]["properties"][self.kb_textField] = {
            "type": "text"
        }

        index_body["mappings"]["properties"][self.kb_metadataField] = {
            "type": "text"
        }

        # Create index
        response = open_search_client.indices.create(self.kb_vector_index_name, body=index_body)
        print('\nCreating index:')
        print(response)

class KnowledgeBaseSetup(VectorStoreSetup):
    def __init__(self, 
                 folder_path, # This is the path to the folder containing the data we want to upload to the knowledge base (kb)
                 region, 
                 account_id, 
                 bucket_name, 
                 kb_name, 
                 embedding_model_arn, 
                 kb_role_name, 
                 init_s3_bucket=False):
        """
        Initialize the KnowledgeBaseSetup class with required AWS details.
        """
        super().__init__(region, account_id, bucket_name, kb_name, embedding_model_arn, kb_role_name)
        self.region = region
        self.account_id = account_id
        self.init_s3_bucket = init_s3_bucket 
        self.folder_path = folder_path

        # Up to you, these are variables:
        self.bucket_name = bucket_name
        self.kb_name = kb_name
        self.kb_role_name = kb_role_name

        # This just creates a name for the datasource - aleatoire we don't care
        self.data_source_name = f"bedrock-kb-datasource-{self.kb_name}"

        # Define embedding model that is chosen:
        self.embedding_model_arn = embedding_model_arn

        # Initialize AWS clients
        self.s3_client = boto3.client('s3', region_name=region)
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.os_serverless_client = boto3.client('opensearchserverless')
        self.sts_client = boto3.client('sts')
        self.sts_caller_identity_arn = self.sts_client.get_caller_identity()['Arn']
        self.bedrock_agent_client = boto3.client('bedrock-agent')

        # Creating default policy names for kb (knowledge base) permissions
        self.kb_bedrock_allow_policy_name = f"bd-kb-bedrock-allow-{self.kb_name}"
        self.kb_aoss_allow_policy_name = f"bd-kb-aoss-allow-{self.kb_name}"
        self.kb_s3_allow_policy_name = f"bd-kb-s3-allow-{self.kb_name}"

        # Creating default name for vector store (ie OpenSearch Service "Collection")
        self.kb_collection_name = f"bedrock-kb-collection-{self.kb_name}"

        # Define what subfolders of the main folder to include in the knowledge base
        self.kb_key = 'kb_documents'

    def config_all_kb_subresources(self):
        """
        Configures the Knowledge Base by creating the necessary resources and ingesting data.
        """
        # Creates role for knowledge base with proper permissions
        self.create_kb_role()

        # Creates permissions for vector store
        self.set_vs_permissions()

        # Create vector store
        self.create_vs()

    def knowledge_base_setup(self):
        """
        Sets up the Knowledge Base by creating the necessary resources and ingesting data.
        """
        self.config_all_kb_subresources()
        if self.init_s3_bucket:
            self.create_s3_bucket()
            self.upload_data_to_s3(self.folder_path)
        self.create_knowledge_base()
        self.set_s3_kb_config()
        self.ingest_data()
        return

    def create_s3_bucket(self):
        """
        Creates an S3 bucket to store the knowledge base data.
        """
        if self.region != 'us-east-1':
            self.s3_client.create_bucket(
                Bucket=self.bucket_name.lower(),
                CreateBucketConfiguration={'LocationConstraint': self.region}
            )
        else:
            self.s3_client.create_bucket(Bucket=self.bucket_name)

    def upload_data_to_s3(self, folder_path):
        """
        Uploads all files within a specified folder to the S3 bucket.

        :param folder_path: Path of the local folder containing files to upload.
        """
        # Upload Knowledge Base files to this s3 bucket
        for f in os.listdir(folder_path):
            self.s3_client.upload_file(folder_path+'/'+f, self.bucket_name, self.kb_key+f)

    def create_knowledge_base(self):
        """
        Creates a Knowledge Base for Amazon Bedrock.
        """
        storage_configuration = {
            'opensearchServerlessConfiguration': {
                'collectionArn': self.collection_arn, 
                'fieldMapping': {
                    'metadataField': self.kb_metadataField,
                    'textField': self.kb_textField,
                    'vectorField': self.kb_vectorField
                },
                'vectorIndexName': self.kb_vector_index_name
            },
            'type': 'OPENSEARCH_SERVERLESS'
        }

        # Creating the knowledge base
        try:
            # ensure the index is created and available
            time.sleep(45)
            self.kb_obj = self.bedrock_agent_client.create_knowledge_base(
                name=self.kb_name, 
                description='KB that contains the bedrock documentation',
                roleArn=self.kb_role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',  # Corrected type
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': self.embedding_model_arn
                    }
                },
                storageConfiguration=storage_configuration
            )

            # Pretty print the response
            pprint.pprint(self.kb_obj)

        except Exception as e:
            print(f"Error occurred: {e}")

    def set_s3_kb_config(self):

        # Define the S3 configuration for your data source
        s3_configuration = {
            'bucketArn': f"arn:aws:s3:::{self.bucket_name}",
            'inclusionPrefixes': [self.kb_key]  
        }

        # Define the data source configuration
        data_source_configuration = {
            's3Configuration': s3_configuration,
            'type': 'S3'
        }

        self.knowledge_base_id = self.kb_obj["knowledgeBase"]["knowledgeBaseId"]
        self.knowledge_base_arn = self.kb_obj["knowledgeBase"]["knowledgeBaseArn"]

        chunking_strategy_configuration = {
            "chunkingStrategy": "FIXED_SIZE",
            "fixedSizeChunkingConfiguration": {
                "maxTokens": 512,
                "overlapPercentage": 20
            }
        }

        # Create the data source
        try:
            # ensure that the KB is created and available
            time.sleep(45)
            self.data_source_response = self.bedrock_agent_client.create_data_source(
                knowledgeBaseId=self.knowledge_base_id,
                name=self.data_source_name,
                description='DataSource for the bedrock documentation',
                dataSourceConfiguration=data_source_configuration,
                vectorIngestionConfiguration = {
                    "chunkingConfiguration": chunking_strategy_configuration
                }
            )

            # Pretty print the response
            pprint.pprint(self.data_source_response)

        except Exception as e:
            print(f"Error occurred: {e}")

    def ingest_data(self):
        """
        Ingests data into the Knowledge Base.
        """
        # Start an ingestion job
        data_source_id = self.data_source_response["dataSource"]["dataSourceId"]
        _ = self.bedrock_agent_client.start_ingestion_job(
            knowledgeBaseId=self.knowledge_base_id, 
            dataSourceId=data_source_id 
        )
        return
    
