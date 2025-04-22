# facial_recognition/management/commands/preprocess_faces.py
from django.core.management.base import BaseCommand
from interno.models import Interno
import face_recognition
import json
from PIL import Image
import numpy as np
import os


class Command(BaseCommand):
    help = 'Gera codificações faciais baseadas nas fotos dos internos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prontuario',
            type=int,
            help='Processa apenas um interno específico pelo prontuário'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força reprocessamento mesmo para internos com codificação existente'
        )

    def handle(self, *args, **options):
        queryset = Interno.objects.exclude(foto__isnull=True)

        if not options['force']:
            queryset = queryset.filter(codificacao_facial__isnull=True)

        if options['prontuario']:
            queryset = queryset.filter(prontuario=options['prontuario'])

        total = queryset.count()
        self.stdout.write(f"Iniciando processamento de {total} internos...")

        for i, interno in enumerate(queryset, 1):
            for i, interno in enumerate(queryset, 1):
                try:
                    self.stdout.write(f"\nProcessando {i}/{total}: {interno.nome} (Prontuário: {interno.prontuario})")

                    if not interno.foto:
                        self.stdout.write(self.style.WARNING("Interno sem foto, pulando..."))
                        continue

                    if not os.path.exists(interno.foto.path):
                        self.stdout.write(self.style.ERROR("Arquivo de foto não encontrado!"))
                        continue

                    image = face_recognition.load_image_file(interno.foto.path)
                    face_locations = face_recognition.face_locations(image)

                    if not face_locations:
                        self.stdout.write(self.style.WARNING("Nenhum rosto detectado na foto!"))
                        continue

                    encodings = face_recognition.face_encodings(image, known_face_locations=[face_locations[0]])

                    if not encodings:
                        self.stdout.write(self.style.WARNING("Não foi possível gerar codificação facial!"))
                        continue

                    interno.codificacao_facial = json.dumps(encodings[0].tolist())
                    interno.save()

                    self.stdout.write(self.style.SUCCESS("Codificação gerada com sucesso!"))
                    self.stdout.write(
                        f"Localização do rosto: Top={face_locations[0][0]}, Right={face_locations[0][1]}, Bottom={face_locations[0][2]}, Left={face_locations[0][3]}"
                    )

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erro ao processar: {str(e)}"))

        self.stdout.write("\nProcessamento concluído!")