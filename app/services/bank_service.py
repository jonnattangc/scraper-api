import logging
from scrapers.mimasoneria import Mimasoneria
from services.security_service import SecurityService


class BankService:
    """Servicio de scraping bancario (actualmente reutiliza Mimasoneria)."""

    def __init__(self):
        pass

    def request_process(self, request, subpath):
        logging.info(f"[BankService] Recv {request.method} Context: /bank/{subpath}")
        security = SecurityService()
        json_data, path, http_code = security.preproccess_request(request, subpath)
        del security

        if http_code != 200 or json_data is None:
            return json_data, http_code

        if path and "login" in path:
            user = json_data.get("username")
            pwrd = json_data.get("password")
            if user and pwrd:
                try:
                    with Mimasoneria() as scraper:
                        grade, name = scraper.login(user, pwrd)
                    return {"message": "Servicio ejecutado exitosamente", "grade": grade, "name": name}, 200
                except Exception as e:
                    logging.error(f"[BankService] Error en login: {e}")
                    return {"message": "Error en scraping"}, 500

        return {"message": "Servicio ejecutado exitosamente"}, 200
