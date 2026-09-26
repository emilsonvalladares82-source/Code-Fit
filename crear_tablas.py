import sys

from app import setup


if __name__ == '__main__':
	try:
		initialized = setup()
	except Exception as error:
		print(f'No se pudo inicializar PostgreSQL: {error}')
		sys.exit(1)

	if not initialized:
		sys.exit(1)

	print('Esquema de CodeFit inicializado correctamente en PostgreSQL.')
