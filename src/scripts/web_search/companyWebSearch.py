from tavily import TavilyClient
import os
import boto3
import json

def get_secret():

    secret_name = "TAVILY_API_KEY_3"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']

    secret = json.loads(secret)['TAVILY_API_KEY_3']

    # Your code goes here.
    return secret

TAVILY_API_KEY = get_secret()
# else:W
#     TAVILY_API_KEY = os.environ['TAVILY_API_KEY']

class companyWebSearch():

    def __init__(self):
        self._set_client()

    def _set_client(self):
        self.client = TavilyClient(api_key=TAVILY_API_KEY)

    def search_context(self, query):
        """
        Can be used for building initial LLM context, or for getting search results real time for a given user query.
        """
        context = self.client.search(query, include_answer=True)
        return context['answer'] # Return the summarized answer directly
    
    def get_company_latest_innovation(self, company_name):
        """
        Get the latest innovation from a company.
        """
        query = "Latest innovation from " + company_name
        context = self.search_context(query)
        return context
    
    def get_company_quarterly_outlook(self, company_name):
        """
        Get the quarterly outlook of a company.
        """
        query = "Quarterly outlook of " + company_name + " Q3 Q4 2024"
        context = self.search_context(query)
        return context
    
    def get_bad_media_press(self, company_name):
        """
        Get bad media press for a company.
        """
        query = "What is the latest bad news about google" + company_name + "?"
        context = self.search_context(query)
        return context
    
    def get_good_media_press(self, company_name):
        """
        Get good media press for a company.
        """
        query = "What is the latest good news about google " + company_name +"?"
        context = self.search_context(query)
        return context
    
    def get_company_competitors(self, company_name):
        """
        Get competitors of a company.
        """
        query = "Main competitors of " + company_name
        context = self.search_context(query)
        return context
    
    def get_industry_info(self, industry_name):
        """
        Get industry information for a company.
        """
        query = "Current trends in the " + industry_name + " industry" + " Q3 Q4 2024"
        context = self.search_context(query)
        return context
    
    def get_sub_sector_info(self, sub_sector_name):
        """
        Get sub-sector information for a company.
        """
        query = "Current trends in the " + sub_sector_name + " sub-sector" + " Q3 Q4 2024"
        context = self.search_context(query)
        return context
    
    def get_geolocation_market_info(self, country):
        """
        Get geolocation information for a company.
        """
        query = "How is the market in " + country + " doing right now? Relevant statistics." + " Q3 Q4 2024"
        context = self.search_context(query)
        return context
    
    def get_world_economy_info(self):
        """
        Get world economy information for a company.
        """
        query = "How is the world economy doing right now? Relevant statistics."  + " Q3 Q4 2024"
        context = self.search_context(query)
        return context

    def get_board_member_info(self, member_name, company_name):
        """
        Get information on a board member.
        """
        query = f"Who is {member_name} and how are they related to {company_name}? Is he invested in other sectors or company?"
        context = self.search_context(query)
        return context

    def get_company_search_results(self, 
                                   company_name, 
                                   necessary_keys,
                                   industry_name,
                                   sub_sector_name,
                                   country, members):
        """
        Performs multiple pre-defined searches to get a comprehensive overview of a company.
        """
        if 'company_search_results' in self.__dict__:
            print("Returning cached search results")
            return self.company_search_results
        
        # Get new company innovations
        company_innovation = self.get_company_latest_innovation(company_name) if necessary_keys['innovation'] else None

        # Get company quarterly outlook
        company_financials = self.get_company_quarterly_outlook(company_name) if necessary_keys['quarterly_outlook'] else None

        # Bad media press?
        company_bad_social_mentions = self.get_bad_media_press(company_name) if necessary_keys['bad_social_mentions'] else None

        # Good media press?
        company_good_social_mentions = self.get_good_media_press(company_name) if necessary_keys['good_social_mentions'] else None

        # Get company competitors
        company_competitors = self.get_company_competitors(company_name) if necessary_keys['competitors'] else None

        # Get industry information
        industry_info = self.get_industry_info(industry_name) if necessary_keys['industry'] else None

        # Get sub-sector information
        sub_sector_info = self.get_sub_sector_info(sub_sector_name) if necessary_keys['sub_sector'] else None

        # Get geolocation information
        geolocation_info = self.get_geolocation_market_info(country) if necessary_keys['geolocation'] else None

        # Get world economy information
        world_economy_info = self.get_world_economy_info() if necessary_keys['world_economy'] else None

        # Get board member information
        board_info = {}
        for member in members:
            board_info[member['name']] = self.get_board_member_info(member['name'], company_name)
            

        self.company_search_results = {
            'innovation': company_innovation,
            'quarterly_outlook': company_financials,
            'bad_social_mentions': company_bad_social_mentions,
            'good_social_mentions': company_good_social_mentions,
            'competitors': company_competitors,
            'industry': industry_info,
            'sub_sector': sub_sector_info,
            'geolocation': geolocation_info,
            'world_economy': world_economy_info,
            'board_members': board_info
        }
        return self.company_search_results

class initialLLMContext(companyWebSearch):
    def __init__(self,
                 company_ticker,
                 company_name,
                 industry_name,
                 sub_sector_name,
                 country,
                 company_description,
                 board_members,
                 vars: dict,
                 search_selection: dict):
        """
        Parameters
        ----------
        company_ticker : str
            Ticker symbol of the company.
        company_name : str
            Name of the company.
        company_description : str
            Description of the company.
        vars : dict
            Dictionary containing various variables to add to the context of the LLM
        search_selection : dict
            Dictionary containing the search features to add, values are booleans
        """

        # Initialize the companyWebSearch class
        all_keys = list(search_selection.keys())
        necessary_keys = ['innovation', 
                          'quarterly_outlook', 
                          'bad_social_mentions', 
                          'good_social_mentions', 
                          'competitors',
                          'industry',
                          'sub_sector',
                          'geolocation',
                          'world_economy']
        for key in necessary_keys:
            if key not in all_keys:
                search_selection[key] = False

        super().__init__()
        self.company_ticker = company_ticker
        self.company_name = company_name
        self.company_description = company_description
        self.industry_name = industry_name
        self.sub_sector_name = sub_sector_name
        self.country = country
        self.vars = vars
        self.search_selection = search_selection
        self.board_members = board_members

    def build_context(self,
                      search_results):
        """
        Builds the context in Markdown format for the LLM.
        """
        context = f"""
        # ADDITIONAL CONTEXT:
        ## Company Ticker: {self.company_ticker}
        ## Company: {self.company_name}
        ## Description: {self.company_description}
        """

        # Add in the selected search categories
        for key, value in search_results.items():
            if type(value) == dict:
                context += f"### {key.capitalize()}\n"
                for sub_key, sub_value in value.items():
                    context += f"#### {sub_key.capitalize()}\n{sub_value}\n"
            if value is not None:
                context += f"### {key.capitalize()}\n{value}\n"

        # Add in additional interesting vars if available
        if self.vars is not None:
            context += "### Additional interesting variables"
            for key, value in self.vars.items():
                context += f"- {key}: {value}\n"

        return context

    def create_context(self):
        """
        Creates the context for the LLM.
        """
        search_results = self.get_company_search_results(
            self.company_name, 
            self.search_selection,
            self.industry_name,
            self.sub_sector_name,
            self.country,
            self.board_members
            )
        context = self.build_context(search_results)
        return context