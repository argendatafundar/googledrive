from abc import ABC as AbstractBaseClass
from abc import abstractmethod

class LazyHttpRequest[A, B](AbstractBaseClass):
    @abstractmethod
    def execute(self, http = None, num_retries = 0) -> B:
        """Execute the request.

        Args:
        http: httplib2.Http, an http object to be used in place of the
                one the HttpRequest request object was constructed with.
        num_retries: Integer, number of times to retry with randomized
                exponential backoff. If all retries fail, the raised HttpError
                represents the last request. If zero (default), we attempt the
                request only once.

        Returns:
        A deserialized object model of the response body as determined
        by the postproc.

        Raises:
        googleapiclient.errors.HttpError if the response was not a 2xx.
        httplib2.HttpLib2Error if a transport error has occured.
        """
        raise NotImplementedError()