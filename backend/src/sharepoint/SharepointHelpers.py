import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import requests
import json
from model.input import SharepointHelperConfig
from model.common import (SharepointToken, AzureADGroupList, SharepointSite,
                          SharepointSiteList)


"""
The `SharepointHelper` class is a Python class that provides methods for interacting with SharePoint sites and retrieving information about user group membership. It uses the Microsoft Graph API to authenticate and make requests to the SharePoint API.

Example Usage:
    # Create a SharepointHelperConfig object with the necessary credentials
    config = SharepointHelperConfig(client_id='your_client_id', client_secret='your_client_secret', tenant_id='your_tenant_id')

    # Create a SharepointHelper object with the config
    sharepoint_helper = SharepointHelper(config=config)

    # Get an access token
    token = sharepoint_helper._get_token()
    print(token.access_token)

    # Get the Azure AD groups that a user belongs to
    user_id = '<user_id>'
    user_groups = sharepoint_helper.get_user_group_membership(user_id=user_id)
    print(user_groups)

    # Get a list of SharePoint sites
    sites = sharepoint_helper.list_sites()
    print(sites)
"""
class SharepointHelper:

    def __init__(self, config: SharepointHelperConfig) -> None:
        self.config = config

    def _get_token(self) -> SharepointToken:
        """
        Obtain an access token from the Microsoft Graph API using the client credentials flow.

        Returns:
            SharepointToken: The access token obtained from the Microsoft Graph API.

        Example Usage:
            config = SharepointHelperConfig(client_id='your_client_id', client_secret='your_client_secret', tenant_id='your_tenant_id')
            sharepoint_helper = SharepointHelper(config=config)
            token = sharepoint_helper._get_token()
            print(token.access_token)
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": "https://graph.microsoft.com/.default"
        }
        url = f"https://login.microsoftonline.com/{self.config.tenant_id}/oauth2/v2.0/token"
        try:
            req = requests.get(url=url, headers=headers, data=body)
            token = json.loads(req.content)
            self.token = SharepointToken(**token)
            return self.token
        except Exception as err:
            print(err)
            raise err

    def get_user_group_membership(self, user_id: str) -> AzureADGroupList:
        """
        Retrieves the Azure AD groups that a user belongs to.

        Args:
            user_id (str): The ID of the user for whom to retrieve the group membership.

        Returns:
            AzureADGroupList: A list of Azure AD groups that the user belongs to.
        """
        self._get_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token.access_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/transitiveMemberOf?$select=displayName,id,proxyAddresses"
        try:
            req = requests.get(url=url, headers=headers)
            req.raise_for_status()
            content = json.loads(req.content)
            group_list_raw: list = content["value"]
            group_list_raw_parsed = []
            for group in group_list_raw:
                del group["@odata.type"]
                if "proxyAddresses" in group:
                    group_list_raw_parsed.append(group)

            group_list = AzureADGroupList(value=group_list_raw_parsed)
            return group_list
        except requests.HTTPError as err:
            print(err)
            raise err

    def list_sites(self) -> SharepointSiteList:
        """
        Retrieves a list of SharePoint sites using the Microsoft Graph API.

        Returns:
            SharepointSiteList: A SharepointSiteList object containing the list of SharePoint sites.
        """
        self._get_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token.access_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/sites?search=*&$select=displayName,id,name,webUrl"
        print(url)
        try:
            req = requests.get(url=url, headers=headers)
            req.raise_for_status()
            content = json.loads(req.content)
            site_list_raw = content["value"]
            site_list_parsed = []
            for site in site_list_raw:
                site_ids = site["id"].split(",")
                site["companyId"] = site_ids[0]
                site["siteId1"] = site_ids[1]
                site["siteId2"] = site_ids[2]
                site_list_parsed.append(site)

            site_list = SharepointSiteList(value=site_list_parsed)
            return site_list
        except requests.HTTPError as err:
            print(err)
            raise err

    def check_user_belong_to_site(self, user_group_list: AzureADGroupList, site_list_to_check: SharepointSiteList) -> SharepointSiteList:
        """
        Checks if a user belongs to a specific site by comparing the user's group membership with a list of sites to check.

        Args:
            user_group_list (AzureADGroupList): A list of Azure AD groups that the user belongs to.
            site_list_to_check (SharepointSiteList): A list of sites to check if the user belongs to.

        Returns:
            SharepointSiteList: A list of sites that the user belongs to.
        """
        user_site_belong_list = []
        for site in site_list_to_check.value:
            for group in user_group_list.value:
                if site.siteId1 in group.proxyAddresses[0]:
                    user_site_belong_list.append(site)

        return SharepointSiteList(value=user_site_belong_list)
    
    def get_site_by_name(self, site_name: str) -> SharepointSite:
        self._get_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token.access_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/sites?search={site_name}&$select=displayName,id,name,webUrl"
        try:
            req = requests.get(url=url, headers=headers)
            req.raise_for_status()
            content = json.loads(req.content)
            site_raw = content["value"][0]
            site_ids = site_raw["id"].split(",")
            site_raw["companyId"] = site_ids[0]
            site_raw["siteId1"] = site_ids[1]
            site_raw["siteId2"] = site_ids[2]
            site_parsed = SharepointSite(**site_raw)
            return site_parsed
        except requests.HTTPError as err:
            print(err)
            raise err
    
    def check_user_belong_to_site_flow(self, user_id: str, list_site_name: list[str]) -> SharepointSiteList:
        user_group_membership = self.get_user_group_membership(user_id=user_id)
        sites_to_check = []
        for site_name in list_site_name:
            site_info = self.get_site_by_name(site_name=site_name)
            sites_to_check.append(site_info)
        sites_to_check = SharepointSiteList(value=sites_to_check)
        return self.check_user_belong_to_site(user_group_list=user_group_membership, site_list_to_check=sites_to_check)
