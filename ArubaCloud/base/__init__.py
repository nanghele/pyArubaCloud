import json
from abc import ABCMeta, abstractmethod

from ArubaCloud.helper import Http
import jsonpickle


class JsonInterfaceBase(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    def gen_def_json_scheme(self, req, method_fields=None):
        """
        Generate the scheme for the json request.
        :param req: String representing the name of the method to call
        :param method_fields: A dictionary containing the method-specified fields
        :rtype : json object representing the method call
        """
        json_dict = dict(
            ApplicationId=req,
            RequestId=req,
            SessionId=req,
            Password=self.auth.password,
            Username=self.auth.username
        )
        if method_fields is not None:
            json_dict.update(method_fields)
        self.logger.debug(json.dumps(json_dict))
        return json.dumps(json_dict)

    def call_method_post(self, method, json_scheme, debug=False):
        url = '{}/{}'.format(self.wcf_baseurl, method)
        headers = {'Content-Type': 'application/json', 'Content-Length': str(len(json_scheme))}
        response = Http.post(url=url, data=json_scheme, headers=headers)
        parsed_response = json.loads(response.content)
        if response.status_code != 200:
            from ArubaCloud.base.Errors import MalformedJsonRequest
            raise MalformedJsonRequest("Request: {}, Status Code: {}".format(json_scheme, response.status_code))
        if parsed_response['Success'] is False:
            from ArubaCloud.base.Errors import RequestFailed
            raise RequestFailed("Request: {}, Response: {}".format(json_scheme, parsed_response))
        if debug is True:
            msg = "Response Message: {}\nHTTP Status Code: {}".format(parsed_response, response.status_code)
            self.logger.debug(msg)
            print(msg)
        return parsed_response


class IRequest(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abstractmethod
    def commit(self):
        raise NotImplementedError


# noinspection PyPep8Naming
class Request(IRequest):

    def __init__(self, logger=None, Username=str(), Password=str(), SessionId=None, ApplicationId=None, RequestId=None,
                 uri=None):
        """
        :type logger: ArubaLog
        :type Username: str
        :type Password: str
        :type SessionId: str
        :type ApplicationId: str
        :type RequestId: str
        :type uri: str
        :param logger: Logger object
        :param Username: ArubaCloud Service Login Username
        :param Password: ArubaCloud Service Login Password
        :param SessionId: Can be Null, otherwise the current SessionId
        :param ApplicationId: Same as RequestId
        :param RequestId: The name of the Request
        :param uri: WCF base URI
        """
        super(Request, self).__init__()
        self.logger = logger
        self.Username = Username
        self.Password = Password
        self.SessionId = SessionId if SessionId is not None else self.__class__.__name__
        self.ApplicationId = ApplicationId if ApplicationId is not None else self.__class__.__name__
        self.RequestId = RequestId if RequestId is not None else self.__class__.__name__
        self.uri = uri

    def _commit(self):
        """
        :return: (dict) Response object content
        """
        assert self.uri is not None, Exception("BadArgument: uri property cannot be None")
        url = '{}/{}'.format(self.uri, self.__class__.__name__)
        serialized_json = jsonpickle.encode(self, unpicklable=False)
        headers = {'Content-Type': 'application/json', 'Content-Length': str(len(serialized_json))}
        response = Http.post(url=url, data=serialized_json, headers=headers)
        content = jsonpickle.decode(response.content.decode("utf-8"))
        if response.status_code != 200:
            from ArubaCloud.base.Errors import MalformedJsonRequest
            raise MalformedJsonRequest("Request: {}, Status Code: {}".format(serialized_json, response.status_code))
        if content['Success'] is False:
            from ArubaCloud.base.Errors import RequestFailed
            raise RequestFailed("Request: {}, Response: {}".format(serialized_json, response))
        return content

    @abstractmethod
    def commit(self):
        raise NotImplementedError("commit method must be implemented in the real request implementation class")


class Auth(object):
    username = None
    password = None
    token = None
    enc_pwd = None

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
