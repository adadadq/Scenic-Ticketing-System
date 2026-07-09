from fastapi import Depends, Request

from app.core.errors import AppError
from app.repositories.passengers import (
    PassengerTemplateConflictError,
    PassengerTemplateRecord,
    PassengerTemplateRepository,
    get_passenger_template_repository,
)
from app.schemas.passengers import PassengerTemplateDTO, PassengerTemplateRequest
from app.services.auth import AuthService, get_auth_service


class PassengerTemplateService:
    def __init__(self, repository: PassengerTemplateRepository, auth_service: AuthService):
        self.repository = repository
        self.auth_service = auth_service

    def list_templates(self, request: Request) -> list[PassengerTemplateDTO]:
        visitor = self.auth_service.require_registered_visitor(request)
        return [self.to_dto(record) for record in self.repository.list_for_owner(visitor.id)]

    def create_template(self, payload: PassengerTemplateRequest, request: Request) -> PassengerTemplateDTO:
        visitor = self.auth_service.require_registered_visitor(request)
        try:
            record = self.repository.create(
                owner_visitor_id=visitor.id,
                passenger_name=payload.passenger_name,
                id_type=payload.id_type,
                id_number=payload.id_number,
                phone=payload.phone,
            )
        except PassengerTemplateConflictError as exc:
            raise AppError(409, "PASSENGER_TEMPLATE_CONFLICT", "出行人证件已存在") from exc
        return self.to_dto(record)

    def update_template(self, template_id: int, payload: PassengerTemplateRequest, request: Request) -> PassengerTemplateDTO:
        visitor = self.auth_service.require_registered_visitor(request)
        try:
            record = self.repository.update(
                template_id=template_id,
                owner_visitor_id=visitor.id,
                passenger_name=payload.passenger_name,
                id_type=payload.id_type,
                id_number=payload.id_number,
                phone=payload.phone,
            )
        except PassengerTemplateConflictError as exc:
            raise AppError(409, "PASSENGER_TEMPLATE_CONFLICT", "出行人证件已存在") from exc
        if record is None:
            raise AppError(404, "PASSENGER_TEMPLATE_NOT_FOUND", "出行人模板不存在")
        return self.to_dto(record)

    def delete_template(self, template_id: int, request: Request) -> dict:
        visitor = self.auth_service.require_registered_visitor(request)
        deleted = self.repository.delete(template_id=template_id, owner_visitor_id=visitor.id)
        if not deleted:
            raise AppError(404, "PASSENGER_TEMPLATE_NOT_FOUND", "出行人模板不存在")
        return {"deleted": True}

    @staticmethod
    def to_dto(record: PassengerTemplateRecord) -> PassengerTemplateDTO:
        return PassengerTemplateDTO(
            template_id=record.id,
            passenger_name=record.passenger_name,
            id_type=record.id_type,
            id_number=record.id_number,
            phone=record.phone,
        )


def get_passenger_template_service(
    repository: PassengerTemplateRepository = Depends(get_passenger_template_repository),
    auth_service: AuthService = Depends(get_auth_service),
) -> PassengerTemplateService:
    return PassengerTemplateService(repository, auth_service)
