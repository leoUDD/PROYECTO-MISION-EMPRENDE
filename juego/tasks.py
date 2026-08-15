from celery import shared_task


@shared_task
def prueba_celery():
    print(
        "======================================"
    )
    print(
        "CELERY FUNCIONANDO EN SEGUNDO PLANO"
    )
    print(
        "======================================"
    )

    return "OK"