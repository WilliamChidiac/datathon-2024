from web_search.companyWebSearch import initialLLMContext
import boto3
import json

class companyChatbot(initialLLMContext):
    def __init__(self,
                 company_ticker,
                 company_name,
                 industry_name,
                 sub_sector_name,
                 country,
                 company_description,
                 variables: dict,
                 search_selection: dict = None,
                 region='us-west-2'):
        """
        Parameters
        ----------
        company_ticker : str
            Ticker symbol of the company.
        company_name : str
            Name of the company.
        industry_name : str
            Name of the industry.   
        sub_sector_name : str
            Name of the sub-sector.
        country : str
            Country of the company.
        company_description : str
            Description of the company.
        variables : dict
            Dictionary containing various variables to add to the context of the LLM
        search_selection : dict
            Dictionary containing the search features to add, values are booleans. Keys must be the same as below to work properly.

        example search_selection:
        ```
        search_selection = {
                'innovation' : True,
                'quarterly_outlook' : True, 
                'bad_social_mentions' : True, 
                'good_social_mentions' : True,
                'competitors' : True,
                'industry' : True,
                'sub_sector' : True,
                'geolocation' : True,
                'world_economy' : True,
        }
        ```
        """
        self.search_selection = search_selection if search_selection is not None else {
            'innovation' : True,
            'quarterly_outlook' : True, 
            'bad_social_mentions' : True, 
            'good_social_mentions' : True,
            'competitors' : True,
            'industry' : True,
            'sub_sector' : True,
            'geolocation' : True,
            'world_economy' : True,
        }

        super().__init__(company_ticker,
                            company_name,
                            industry_name,
                            sub_sector_name,
                            country,
                            company_description,
                            variables,
                            self.search_selection)
        
        # Initialize the AWS client for the Titan model
        self.bedrock = boto3.client('bedrock-runtime', region_name=region)


        self.industry_name = industry_name
        self.sub_sector_name = sub_sector_name
        self.country = country

    def build_instructions(self):
        """
        Builds the system instructions in Markdown format for the LLM. This should be run after the company ticker is selected.
        """
        search_results = self.get_company_search_results(
                                    self.company_name,
                                    self.search_selection,
                                    self.industry_name,
                                    self.sub_sector_name,
                                    self.country
                                    )
        self.system_instructs = self.build_context(search_results)
        self.instruct_overview = f"""
        ## OVERVIEW: 
        You are a helpful financial assistant that provides financial analysts with pertinent information that can help them in their analyses.\n
        User's will ask you questions, you should use the information below to enhance your response.\n
        Make sure to think analytically about the specified company's financial performance and future outlook.\n
        Think step by step.\n
        """
        self.system_instructs += self.instruct_overview

    def get_llm_response(self, prompt, system_instructs, past_responses : list =None):
        claude_model_id = "anthropic.claude-3-5-sonnet-20240620-v1:0"  
        messages = [{
            "role": "user",
            "content": prompt
        }]
        if past_responses is not None:
            messages = past_responses + messages
        try:
            # Prepare message payload for Claude

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": 1000,
                "system": system_instructs,
                "messages": messages,
                "temperature": 0.8,
            })  

            # Invoke Claude model
            response = self.bedrock.invoke_model(
                modelId=claude_model_id,
                body=body
            )

            # Decode response
            resp = json.loads(response['body'].read().decode('utf-8'))

            # Extract assistant response
            prev_answer = {
                "role": resp['role'],
                "content": resp['content'][0]['text']
            }

            print(f"Previous answer: {prev_answer}")
            print(f"Messages: {messages}")

            conversation_thread = messages + [prev_answer]
                        
            return {
                'response': prev_answer['content'],
                'past_responses': conversation_thread
            }

        except Exception as e:
            print(f"Error getting response: {str(e)}")
        
if __name__ == "__main__":
    # Search selection (selection from selectbox)
    search_selection = {
        'innovation' : True,
        'quarterly_outlook' : True, 
        'bad_social_mentions' : True, 
        'good_social_mentions' : True,
        'competitors' : True,
        'industry' : True,
        'sub_sector' : True,
        'geolocation' : True,
        'world_economy' : True,
    }

    obj = companyChatbot(
        company_ticker="GOOGL",
        company_name="Google",
        industry_name="Technology",
        sub_sector_name="Internet",
        country="USA",
        company_description=None,
        variables=None,
        search_selection=search_selection,
    )

    obj.build_instructions()
    print(obj.get_llm_response("What is the quarterly outlook for Google?"))
