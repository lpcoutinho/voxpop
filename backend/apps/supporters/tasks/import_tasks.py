import csv
import io
import logging
from datetime import date, datetime

from celery import shared_task
from django.db import IntegrityError
from tenant_schemas_celery.task import TenantTask

logger = logging.getLogger(__name__)

VALID_FIELDS = {
    'name', 'first_name', 'last_name',
    'phone', 'email', 'cpf', 'city', 'neighborhood',
    'state', 'zip_code', 'electoral_zone', 'electoral_section',
    'birth_date', 'gender',
}


def parse_date(value: str) -> date | None:
    if not value or not value.strip():
        return None
    value = value.strip()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d'):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def parse_gender(value: str) -> str:
    if not value or not value.strip():
        return ''
    value = value.strip().upper()
    if value in ('M', 'F', 'O'):
        return value
    if value in ('MASCULINO', 'MALE'):
        return 'M'
    if value in ('FEMININO', 'FEMALE'):
        return 'F'
    if value in ('OUTRO', 'OTHER', 'NB', 'NAO_BINARIO'):
        return 'O'
    return ''


def clean_phone(value: str) -> str:
    if not value:
        return ''
    digits = ''.join(c for c in value if c.isdigit() or c == '+')
    if digits and not digits.startswith('+'):
        digits = '+' + digits
    return digits


@shared_task(bind=True, base=TenantTask, queue='default')
def process_import_job(self, import_job_id: int) -> dict:
    from apps.supporters.models import ImportJob, Supporter

    try:
        job = ImportJob.objects.get(id=import_job_id)
    except ImportJob.DoesNotExist:
        logger.error(f"ImportJob {import_job_id} nao encontrado")
        return {'status': 'error', 'message': 'ImportJob nao encontrado'}

    job.mark_as_processing()

    try:
        file_path = job.file_path
        column_mapping = job.column_mapping or {}

        if file_path.lower().endswith('.csv'):
            result = _process_csv(job, column_mapping)
        elif file_path.lower().endswith(('.xlsx', '.xls')):
            result = _process_excel(job, column_mapping)
        else:
            raise ValueError(f"Formato nao suportado: {file_path}")

        job.mark_as_completed()
        logger.info(
            f"Importacao concluida: {job.success_count} sucessos, "
            f"{job.error_count} erros, {job.skipped_count} ignorados"
        )
        return result

    except Exception as e:
        logger.exception(f"Erro ao processar importacao {import_job_id}: {e}")
        job.mark_as_failed(str(e)[:500])
        return {'status': 'error', 'message': str(e)}


def _build_field_to_csv_map(column_mapping: dict, csv_headers: list[str]) -> dict:
    if column_mapping:
        return {v: k for k, v in column_mapping.items()}

    result = {}
    for header in csv_headers:
        normalized = header.strip().lower()
        if normalized in VALID_FIELDS:
            result[normalized] = header
    return result


def _process_csv(job, column_mapping: dict) -> dict:
    from apps.supporters.models import Supporter, Tag

    file_path = job.file_path
    auto_tag_ids = list(job.auto_tags.values_list('id', flat=True))

    with open(file_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not reader.fieldnames:
        raise ValueError("Arquivo CSV vazio ou sem cabecalho")

    job.total_rows = len(rows)
    job.save(update_fields=['total_rows', 'updated_at'])

    field_to_csv = _build_field_to_csv_map(column_mapping, reader.fieldnames)

    for row_idx, row in enumerate(rows, start=2):
        try:
            supporter_data = {}
            for model_field, csv_col in field_to_csv.items():
                value = row.get(csv_col, '').strip() if csv_col else ''
                supporter_data[model_field] = value

            name = supporter_data.get('name', '').strip()
            phone = clean_phone(supporter_data.get('phone', ''))

            if not name:
                job.add_error(row_idx, 'name', 'Nome e obrigatorio')
                continue

            if not phone:
                job.add_error(row_idx, 'phone', 'Telefone e obrigatorio')
                continue

            supporter_data['birth_date'] = parse_date(supporter_data.get('birth_date', ''))
            supporter_data['gender'] = parse_gender(supporter_data.get('gender', ''))
            supporter_data['phone'] = phone

            if Supporter.objects.filter(phone=phone).exists():
                job.increment_skipped()
                continue

            create_kwargs = {
                k: v for k, v in supporter_data.items()
                if k in VALID_FIELDS and v not in ('', None)
            }

            create_kwargs["source"] = Supporter.Source.IMPORT
            supporter = Supporter.objects.create(**create_kwargs)

            if auto_tag_ids:
                supporter.tags.add(*auto_tag_ids)

            supporter.set_as_lead()
            job.increment_success()

        except IntegrityError:
            job.increment_skipped()
        except Exception as e:
            job.add_error(row_idx, 'geral', str(e)[:200])
            logger.debug(f"Erro na linha {row_idx}: {e}")

    return {
        'status': 'completed',
        'total': job.total_rows,
        'success': job.success_count,
        'errors': job.error_count,
        'skipped': job.skipped_count,
    }


def _process_excel(job, column_mapping: dict) -> dict:
    raise ValueError(
        "Importacao de arquivos Excel nao esta disponivel. "
        "Converta o arquivo para CSV e tente novamente."
    )
