import hashlib

def calculate_file_hash(file_content: bytes) -> str:
    """
    Calcula el hash SHA256 de un archivo.

    Args:
        file_content: Contenido del archivo en bytes

    Returns:
        Hash SHA256 en formato hexadecimal
    """
    return hashlib.sha256(file_content).hexdigest()
