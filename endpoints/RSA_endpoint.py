from fastapi import APIRouter, Depends, Request, HTTPException, Form
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.database import get_db
import app.crud as crud
import logging
from app import RSA_fast
import json
from app.logic import get_client_ip, get_current_user_from_token
import os

# Настройка шаблонов
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
templates = Jinja2Templates(directory=templates_dir)

router = APIRouter(prefix="/RSA", tags=["RSA"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Страница генерации ключей
@router.get("/keys", response_class=HTMLResponse)
async def generate_rsa_keys(
    request: Request, user = Depends(get_current_user_from_token), db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        # Генерируем ключи
        pub_key, priv_key = RSA_fast.RSA_key_gen_fast() 

        # Сохраняем в базу
        keypair = crud.create_rsa_keypair(
            db, user.id, json.dumps(pub_key), json.dumps(priv_key)
        )

        # Логируем активность
        crud.create_user_activity(
            db,
            user.id,
            "key_generation",
            f"Сгенерированы ключи ID: {keypair.id}",
            get_client_ip(request),
        )
 
        return templates.TemplateResponse(
            "keys.html", 
            {
                "request": request, 
                "user": user,
                "keys": [pub_key, priv_key]
            }
        )

    except Exception as e:
        logger.error(f"❌ Ошибка генерации ключей: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка генерации ключей: {str(e)}"
        )


# Страница шифрования
@router.post("/api/encrypt")
async def rsa_encrypt(
    request: Request,
     user = Depends(get_current_user_from_token),
    text: str = Form(...),
    key_id: int = Form(None),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        # Получаем ключ
        if key_id:
            keypair = crud.get_keypair(db, key_id)
            if not keypair or keypair.user_id != user.id:
                raise HTTPException(status_code=403, detail="Доступ к ключу запрещен")
            pub_key = json.loads(keypair.public_key)
        else:
            # Генерируем временные ключи
            pub_key, _ = RSA_fast.RSA_key_gen_fast()
            key_id = None

        # Шифруем текст
        cipher = RSA_fast.RSA_encrypt_fast(text, pub_key)

        # Сохраняем операцию
        operation = crud.create_rsa_operation(
            db, user.id, "encrypt", text, json.dumps(cipher), key_id
        )

        # Логируем активность
        crud.create_user_activity(
            db,
            user.id,
            "encrypt",
            f"Зашифрован текст длиной {len(text)} символов",
            get_client_ip(request),
        )

        return operation.id, cipher, pub_key,

    except Exception as e:
        logger.error(f"❌ Ошибка шифрования: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка шифрования: {str(e)}")


# Страница расшифрования
@router.post("/api/decrypt")
async def rsa_decrypt(
    request: Request,
    user = Depends(get_current_user_from_token),
    cipher: str = Form(...),
    key_id: int = Form(...),
    db: Session = Depends(get_db),
):
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    try:
        # Получаем ключ
        keypair = crud.get_keypair(db, key_id)
        if not keypair or keypair.user_id != user.id:
            raise HTTPException(status_code=403, detail="Доступ к ключу запрещен")

        priv_key = json.loads(keypair.private_key)

        # Парсим cipher
        cipher_list = json.loads(cipher)

        # Расшифровываем
        text = RSA_fast.RSA_decrypt_fast(cipher_list, priv_key)
        text_str = "".join(text)

        # Сохраняем операцию
        operation = crud.create_rsa_operation(
            db, user.id, "decrypt", json.dumps(cipher_list), text_str, key_id
        )

        # Логируем активность
        crud.create_user_activity(
            db,
            user.id,
            "decrypt",
            f"Расшифрован текст длиной {len(text_str)} символов",
            get_client_ip(request),
        )

        return operation.id, text_str

    except Exception as e:
        logger.error(f"❌ Ошибка расшифрования: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка расшифрования: {str(e)}")


# История операций
@router.get("/history")
async def history_page(
    request: Request, user = Depends(get_current_user_from_token), db: Session = Depends(get_db)
):
    if user == None:
        return RedirectResponse(url="/login", status_code=303)

    # Получаем операции пользователя
    operations = crud.get_user_operations(db, user.id, limit=100)

    return request, user, operations