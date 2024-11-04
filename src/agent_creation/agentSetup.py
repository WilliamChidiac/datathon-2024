from knowledgeBaseSetup import KnowledgeBaseSetup
import boto3
import json
import time
from pprint import pprint
import uuid

class AgentSetup(KnowledgeBaseSetup):
    def __init__(self, 
                 folder_path,
                 region, 
                 account_id, 
                 agent_role_name,
                 agent_name,
                 bucket_name=None,
                 kb_name=None, 
                 kb_role_name=None,
                 embedding_model_arn="arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v1", 
                 model_id="amazon.titan-text-express-v1",
                 init_s3_bucket=False,
        ):

        if kb_role_name == agent_role_name:
            raise ValueError("The Knowledge Base Role Name and Agent Role Name must be different.")

        super().__init__(folder_path, region, account_id, bucket_name, kb_name, embedding_model_arn, kb_role_name, init_s3_bucket)

        self.agent_role_name = agent_role_name
        self.agent_name = agent_name
        self.model_id = model_id
        self.bedrock_agent_client = boto3.client('bedrock-agent')

        self.bedrock_agent_kb_allow_policy_name = f"bda-kb-allow-{self.kb_name}"
        self.bedrock_agent_bedrock_allow_policy_name = f"bda-bedrock-allow-{self.kb_name}"

        self.bedrock_agent_runtime_client = boto3.client('bedrock-agent-runtime')

    def add_knowledge_base(self):
        if (self.bucket_name is None) or (self.kb_name is None) or (self.kb_role_name is None):
            raise ValueError("Please provide a bucket name, kb_name and kb_role_name to add a knowledge base.")
        self.knowledge_base_setup()
        self.includes_knowledge_base = True

    def setup_agent(self, agent_instructions, agent_description="Agent for financial analysis."):   
        self.set_agent_permissions()
        self.create_agent(agent_instructions, agent_description)

    def define_bedrock_allow_policy(self):
        """
        Creates a policy that allows the agent to use bedrock
        """
        # Create IAM policies for agent
        bedrock_agent_bedrock_allow_policy_statement = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AmazonBedrockAgentBedrockFoundationModelPolicy",
                    "Effect": "Allow",
                    "Action": "bedrock:*",
                    "Resource": [ 
                        f"arn:aws:bedrock:{self.region}::foundation-model/{self.model_id}"
                    ]
                }
            ]
        }

        bedrock_policy_json = json.dumps(bedrock_agent_bedrock_allow_policy_statement)

        agent_bedrock_policy = self.iam_client.create_policy(
            PolicyName=self.bedrock_agent_bedrock_allow_policy_name,
            PolicyDocument=bedrock_policy_json
        ) 
        self.agent_bedrock_policy = agent_bedrock_policy
        return agent_bedrock_policy["Policy"]["Arn"]

    def define_kb_retrieval_policy(self):
        """
        Creates a policy that allows the agent to access the knowledge base
        """
        bedrock_agent_kb_retrival_policy_statement = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:Retrieve"
                    ],
                    "Resource": [
                        self.knowledge_base_arn
                    ]
                }
            ]
        }
        bedrock_agent_kb_json = json.dumps(bedrock_agent_kb_retrival_policy_statement)
        agent_kb_schema_policy = self.iam_client.create_policy(
            PolicyName=self.bedrock_agent_kb_allow_policy_name,
            Description=f"Policy to allow agent to retrieve documents from knowledge base.",
            PolicyDocument=bedrock_agent_kb_json
        )
        self.agent_kb_schema_policy = agent_kb_schema_policy
        return agent_kb_schema_policy["Policy"]["Arn"]

    def set_agent_permissions(self):
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
        self.agent_role = self.iam_client.create_role(
            RoleName=self.agent_role_name,
            AssumeRolePolicyDocument=assume_role_policy_document_json
        )

        # Pause to make sure role is created
        time.sleep(10)
            
        self.iam_client.attach_role_policy(
            RoleName=self.agent_role_name,
            PolicyArn=self.define_bedrock_allow_policy()
        )

        if "includes_knowledge_base" in self.__dict__: # Define retrieval policy for data in vectorstore
            self.iam_client.attach_role_policy(
                RoleName=self.agent_role_name,
                PolicyArn=self.define_kb_retrieval_policy()
            )

    def create_agent(self, agent_instructions, agent_description="Agent for financial analysis."):
        # Create Agent
        response = self.bedrock_agent_client.create_agent(
            agentName=self.agent_name,
            agentResourceRoleArn=self.agent_role['Role']['Arn'],
            description=agent_description,
            idleSessionTTLInSeconds=1800,
            foundationModel=self.model_id,
            instruction=agent_instructions,
        )
        agent_id = response['agent']['agentId']
        print("------AGENT CREATED------")
        print(f"Agent ID: {agent_id}")
        print("-------------------------")
        time.sleep(30) # Wait for agent to be created
        # Associate kb
        if "includes_knowledge_base" in self.__dict__: # Define retrieval policy for data in vectorstore
            _ = self.bedrock_agent_client.associate_agent_knowledge_base(
            agentId=agent_id,
            agentVersion='DRAFT',
            description=f'Use the information in the {self.kb_name} knowledge base to provide accurate responses to financial questions.',
            knowledgeBaseId=self.knowledge_base_id 
            )
            print("------ADDED KNOWLEDGE BASE------")
            print(f"Knowledge Base ID: {self.knowledge_base_id}")
            print("--------------------------------")

        _ = self.bedrock_agent_client.prepare_agent(agentId=agent_id)

        self.agent_id = agent_id
        return agent_id
    
    def create_agent_alias(self, agent_alias_name):
        # Pause to make sure agent is prepared
        print("------CREATING AGENT ALIAS------")
        time.sleep(30)
        self.agent_alias = self.bedrock_agent_client.create_agent_alias(
            agentId=self.agent_id,
            agentAliasName=agent_alias_name
        )
        print("------AGENT ALIAS CREATED------")
        print(f"Agent Alias ID: {self.agent_alias['agentAlias']['agentAliasId']}")
        print("--------------------------------")
        print("Waiting for agent alias to be ready...")
        # Pause to make sure agent alias is ready
        time.sleep(30)
        return

    def test_agent(self, prompt):
        # Extract the agentAliasId from the response
        agent_alias_id = self.agent_alias['agentAlias']['agentAliasId']

        ## create a random id for session initiator id
        session_id:str = str(uuid.uuid1())
        enable_trace:bool = True
        end_session:bool = False

        # invoke the agent API
        agentResponse = self.bedrock_agent_runtime_client.invoke_agent(
            inputText=prompt,
            agentId=self.agent_id,
            agentAliasId=agent_alias_id, 
            sessionId=session_id,
            enableTrace=enable_trace, 
            endSession= end_session
        )

        pprint(agentResponse)