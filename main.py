import uvicorn
from uvicorn.config import LOGGING_CONFIG

from fastapi import FastAPI, status, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html
from fastapi.routing import APIRoute
from fastapi.openapi.utils import get_openapi

# modules in current folder
import auth
import endpoint

class CustomFastAPI():
    def __init__(self):
        
        self.app = FastAPI(
            docs_url = None,
            redoc_url = None,
        )

        self.app.mount("/static", StaticFiles(directory="static"))
        
        self.app.include_router(endpoint.router)
        
        #Override default openapi generation function
        self.app.openapi = self.custom_openapi

        self.swagger_html = None
        self.openapi_user = None
        self.openapi_privilege = auth.AccessPrivilege.default
        
        #get access privilege from GET openapi.json request
        @self.app.middleware("http")
        async def custom_http_handler(request: Request, call_next):
            if "openapi.json" in request.url.path:
                self.openapi_user = None
                
                if "authorization" in request.headers:
                    token = request.headers["authorization"].replace("bearer ", "")
                    if token != "":
                        try:
                            self.openapi_user = auth.get_current_user(token=token)
                        except HTTPException as e:
                            print(f'[openapi] validating user failed, login again: {e.detail}')

                response = await call_next(request)
            else:
                response = await call_next(request)
            
            return response
        
        @self.app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            if self.swagger_html == None:
                with open("./static/swagger-ui.html", "r") as f:
                    self.swagger_html = f.read()
                
            return HTMLResponse(status_code=status.HTTP_200_OK, content=self.swagger_html)
                
        @self.app.get(self.app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
        async def swagger_ui_redirect():
            return get_swagger_ui_oauth2_redirect_html()
        
        #NOTE: Redoc is disabled
        
    def custom_openapi(self):
        route_list = []
        self.openapi_privilege = auth.AccessPrivilege.default
        
        if self.openapi_user != None:
            if self.openapi_user.privilege == auth.AccessPrivilege.general.value:
                self.openapi_privilege = auth.AccessPrivilege.general
            elif self.openapi_user.privilege == auth.AccessPrivilege.admin.value:
                self.openapi_privilege = auth.AccessPrivilege.admin
            elif self.openapi_user.privilege == auth.AccessPrivilege.root.value:
                self.openapi_privilege = auth.AccessPrivilege.root

        for route in self.app.routes:
            if type(route) == APIRoute:
                if route.openapi_extra != None and auth.OpenAPIExtra.access_privilege.value in route.openapi_extra:
                    # To include endpoints from lower privilege
                    # if route.openapi_extra[auth.OpenAPIExtra.access_privilege.value].value >= self.openapi_privilege.value:
                    
                    # To only provide endpoints with right privilege
                    if route.openapi_extra[auth.OpenAPIExtra.access_privilege.value].value == self.openapi_privilege.value:
                        route_list.append(route)
                else:
                    # if access_level is not set, endpoint will be documented when access as root user
                    if self.openapi_privilege.value == auth.AccessPrivilege.root.value:
                        route_list.append(route)
            else:
                route_list.append(route)
                
        openapi_schema = get_openapi(
            title = "Custom_FastAPI",
            version = "0.0",
            description = f'Privilege of current user: {self.openapi_privilege.name}',
            routes = route_list
        )
        
        self.app.openapi_schema = openapi_schema
        
        return self.app.openapi_schema

if __name__ == '__main__':
    fastapi_obj = CustomFastAPI()
    #Uvicorn accidently set the default log config to None in v0.18.0 -> fix in v0.18.2
    uvicorn.run(fastapi_obj.app, host="0.0.0.0", port=8080, log_config=LOGGING_CONFIG, use_colors=True)