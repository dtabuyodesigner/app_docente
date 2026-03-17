from marshmallow import Schema, fields, validate

class AreaSchema(Schema):
    nombre = fields.String(required=True, validate=validate.Length(min=1, error="El nombre no puede estar vacío"))
    etapa_id = fields.Integer(required=True, error_messages={"required": "La etapa_id es obligatoria", "invalid": "etapa_id debe ser un entero válido"})
    modo_evaluacion = fields.String(validate=validate.OneOf(["POR_SA", "POR_CRITERIOS", "GLOBAL"]), load_default="POR_SA")
    tipo_escala = fields.String(validate=validate.OneOf(["NUMERICA_1_4", "INFANTIL_NI_EP_C", "NUMERICA_1_10"]), load_default="NUMERICA_1_4")
    activa = fields.Integer(validate=validate.OneOf([0, 1]), load_default=1)

class CriterioSchema(Schema):
    codigo = fields.String(required=True, validate=validate.Length(min=1, error="El código no puede estar vacío"))
    descripcion = fields.String(required=True, validate=validate.Length(min=1, error="La descripción no puede estar vacía"))
    area_id = fields.Integer(required=True, error_messages={"required": "El area_id es obligatorio", "invalid": "area_id debe ser un entero válido"})
    activo = fields.Integer(validate=validate.OneOf([0, 1]), load_default=1)
    oficial = fields.Integer(validate=validate.OneOf([0, 1]), load_default=1)
