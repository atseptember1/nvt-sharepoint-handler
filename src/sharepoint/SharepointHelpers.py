import json

import requests

from ..model.common import (SharepointToken, AzureADGroupList, SharepointSite,
                            SharepointSiteList)
from ..model.config import SharepointHelperConfig


class SharepointHelper:

    def __init__(self, config: SharepointHelperConfig) -> None:
        self.config = config

    def _get_token(self) -> SharepointToken:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "client_credentials",
            "client_id": self.config.ClientId,
            "client_secret": self.config.ClientSecret,
            "scope": "https://graph.microsoft.com/.default"
        }
        url = f"https://login.microsoftonline.com/{self.config.TenantId}/oauth2/v2.0/token"
        try:
            req = requests.get(url=url, headers=headers, data=body)
            req.raise_for_status()
            token = json.loads(req.content)
            print(token)
            self.token = SharepointToken(
                token_type=token["token_type"],
                expires_in=token["expires_in"],
                ext_expires_in=token["ext_expires_in"],
                access_token=token["access_token"]
            )
            return self.token
        except Exception as err:
            print(err)
            raise err

    def get_user_group_membership(self, user_id: str) -> AzureADGroupList:
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
                print(site)

            site_list = SharepointSiteList(Value=site_list_parsed)
            return site_list
        except requests.HTTPError as err:
            print(err)
            raise err

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

    @classmethod
    def check_user_belong_to_site(cls, user_group_list: AzureADGroupList,
                                  site_list_to_check: SharepointSiteList) -> SharepointSiteList:
        user_site_belong_list = []
        for site in site_list_to_check.value:
            for group in user_group_list.value:
                if site.siteId1 in group.proxyAddresses[0]:
                    user_site_belong_list.append(site)

        return SharepointSiteList(value=user_site_belong_list)

    def check_user_belong_to_site_flow(self, user_id: str, list_site_name: list[str]) -> SharepointSiteList:
        user_group_membership = self.get_user_group_membership(user_id=user_id)
        sites_to_check = []
        for site_name in list_site_name:
            site_info = self.get_site_by_name(site_name=site_name)
            sites_to_check.append(site_info)
        sites_to_check = SharepointSiteList(value=sites_to_check)
        return self.check_user_belong_to_site(user_group_list=user_group_membership, site_list_to_check=sites_to_check)
