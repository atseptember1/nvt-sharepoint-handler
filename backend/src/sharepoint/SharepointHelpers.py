import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import requests
import json
from model.input import SharepointHelperConfig
from model.common import (SharepointToken, AzureADGroupList,
                          SharepointSiteList)


class SharepointHelper:

    def __init__(self, config: SharepointHelperConfig) -> None:
        self.config = config

    def _get_token(self) -> SharepointToken:
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

    def get_user_group_membership(
            self, user_id: str) -> AzureADGroupList:
        self._get_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token.access_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/transitiveMemberOf?$select=displayName,id,proxyAddresses"
        try:
            req = requests.get(url=url, headers=headers)
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

    # def check_user_belong_to_group(self, user_id: str, group_list: list):
    #     self._get_token()
    #     headers = {
    #         "Content-Type": "application/json",
    #         "Authorization": f"Bearer {self.token.access_token}"
    #     }
    #     url = f"https://graph.microsoft.com/v1.0/users/{user_id}/transitiveMemberOf/microsoft.graph.group?$filter=id in ("
    #     for group in group_list:
    #         if group == group_list[-1]:
    #             url = url + f"'{group}')"
    #         else:
    #             url = url + f"'{group}',"

    #     try:
    #         req = requests.get(url=url, headers=headers)
    #         req.raise_for_status()
    #         content = json.loads(req.content)
    #         group_list = content["value"]
    #         return group_list
    #     except requests.HTTPError as err:
    #         print(err)
    #         raise err

    def list_sites(self) -> SharepointSiteList:
        self._get_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token.access_token}"
        }
        url = f"https://graph.microsoft.com/v1.0/sites?search=*&$select=displayName,id,name,webUrl"
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
        user_site_belong_list = []
        for site in site_list_to_check.value:
            for group in user_group_list.value:
                if site.siteId1 in group.proxyAddresses[0]:
                    user_site_belong_list.append(site)

        return SharepointSiteList(value=user_site_belong_list)
