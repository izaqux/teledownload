#
#	@utor Izaqux
#	Python
#

#	Realizar download de arquivos, de grupos ou canais no Telegram

# pip install telethon
# pip install tabulate

import os
import asyncio
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from telethon.errors import (
	SessionPasswordNeededError,
	FloodWaitError,
	ChannelPrivateError,
	ChatAdminRequiredError
)
from tabulate import tabulate
import argparse

class TeleDownload():
	def __init__(self, apiID, apiHash, sessionName='session_teledownload'):
		self.apiID = apiID
		self.apiHash = apiHash
		self.sessionName = sessionName
		self.client = None
		self.downloadInterrupted = False

	async def __aenter__(self):
		# startClient
		self.client = TelegramClient(self.sessionName, self.apiID, self.apiHash)
		await self.client.start()
		return self

	async def __aexit__(self, exc_type, exc, tb):
		# disconnectClient
		if self.client:
			await self.client.disconnect()

	async def checkGC(self, chatID):
		# Verificar ID do chat ou grupo
		try:
			return await self.client.get_entity(chatID)
		except ValueError:
			try:
				# Tenta com username, se começar com @
				if isinstance(chatID, str) and chatID.startswith('@'):
					return await self.client.get_entity(chatID)

				# ID numérico
				if isinstance(chatID, str) and chatID.lstrip('-').isdigit():
					numIDGC = int(chatID)
					# Prefixo -100 para supergrupos
					if numIDGC < 0:
						return await self.client.get_entity(numIDGC)
					else:
						return await self.client.get_entity(int(f"-100{chatID}"))

				# Busca diálogos
				async for dialog in self.client.iter_dialogs():
					if str(dialog.id) == chatID or dialog.name == chatID:
						return dialog.entity

			except Exception as error:
				#logger.error(f"Falha ao resolver chat: {error}")
				raise ValueError(f"Não foi possível encontrar o chat: {chatID}")
				#pass

	async def listChats(self):
		# Lista todos os chats, grupos, canais
		print("\n🔍 Listando todos os chats\n")

		# Armazenar os dados em uma tabela
		tableData = []

		async for dialog in self.client.iter_dialogs():
			entity = dialog.entity


			# Tipo de chat
			if isinstance(entity, Channel):
				chatType = "CANAL" if entity.broadcast else "GRUPO"
			elif isinstance(entity, Chat):
				chatType = "GRUPO"
			elif isinstance(entity, User):
				chatType = "PRIVADO"
			else:
				chatType = "DESCONHECIDO"

			# Formata ID para grupos ou canais
			chatID = entity.id
			if isinstance(entity, (Channel, Chat)):
				chatID = f"-{abs(chatID)}" if not entity.broadcast else f"-100{abs(chatID)}"

			# Link de convite disponível?
			username = f"@{entity.username}" if hasattr(entity, 'username') and entity.username else "Sem link"		

			# Add os dados a tabela
			tableData.append([
				chatType,
				dialog.name, # Nome completo
				str(chatID),
				username
			])

			# Cabeçalhos da tabela
			headers = ["TIPO", "NOME", "ID", "LINK"]

			# Exibe a tabela
			print(tabulate(tableData, headers=headers, tablefmt="grid"))
			print(f"\nTotal de chats listados: {len(tableData)}")

	async def downloadFiles(self, chatID, downFolder=None):
		# Baixar arquivos de um grupo ou canal

		# Chat existe?
		try:
			chat = await self.checkGC(chatID)
		except Exception as error:
			print(f"❌ Erro: Chat não encontrado. Verifique o ID. ({error})")
			return

		downDir = downFolder or f"{chat.title}" # Pasta para salvar arqs
		os.makedirs(downDir, exist_ok=True)

		print(f"✅ Conectado! Monitorando o chat: {chat.title}")
		print(f"📁 Pasta de download: {os.path.abspath(downDir)}")

		# Pega total de msgs no chat
		totalMsgs = await self.client.get_messages(chat, limit=1)
		totalCount = totalMsgs.total
		print(f"📂 Total de mensagens no canal: {totalCount}")

		# Baixa todas as msgs do mais antigo para mais recente
		offsetId = 0
		batchSize = 100  # Número de msgs por lote
		downloadedFiles = 0
		skippedFiles = 0
		failedDownloads = 0

		try:
			while True:
				messages = await self.client.get_messages(
					chat,
					limit=batchSize,
					offset_id=offsetId,
					reverse=True # Mais antigas primeiro
				)

				if not messages:
					break

				for message in messages:
					if not message.file:
						continue

					# Nome do arq
					fileName = os.path.join(
						downDir,
						message.file.name or f"{message.id}{message.file.ext or 'bin'}"
					)

					# Se arq já existe
					if os.path.exists(fileName):
						fileSize = os.path.getsize(fileName)
						if fileSize == message.file.size:
							print(f"⏭️ Arquivo já existe: {fileName}")
							downloadedFiles+=1 # Então soma + 1
							continue
						else:
							# Rmv arq incompleto
							os.remove(fileName)

					print(f"⬇️ Baixando ({downloadedFiles+1}/{totalCount}): {os.path.basename(fileName)}")

					# Baixa o arq
					try:
						tempFileName = fileName + '.tmp'

						def progressCallbackDown(downBytes, totalBytes):
							print(f"\r📥 Progresso: {downBytes/totalBytes:.2%}", end="", flush=True)

						await self.client.download_media(
							message,
							file=fileName,
							progress_callback=progressCallbackDown
						)

						# Se download é completo
						if os.path.getsize(tempFileName) == message.file.size:
							os.rename(tempFileName, fileName)
							print(f"\n✅ Download concluído: {fileName}")
							downloadedFiles+=1
						else:
							raise Exception("Tamanho do arquivo incompatível")

					except Exception as error:
						if os.path.exists(tempFileName):
							os.remove(tempFileName)
						print(f"\n❌ Nome: {fileName} | Erro ao baixar: {error}")
						failedDownloads+=1

				# Atualiza o offset para a próxima página
				if len(messages) < batchSize:
					break
				offsetId = messages[-1].id

		except KeyboardInterrupt:
			self.downloadInterrupted = True
		except Exception as error:
			print(f"\n❌ Erro durante o download: {error}")
		finally:
			print(f"\n\nRelatório de downloads:")
			print(f"✅ Baixados com sucesso: {downloadedFiles}")
			print(f"⏭️ Pulados (já existiam): {skippedFiles}")
			print(f"❌ Falhas no download: {failedDownloads}")

			if self.downloadInterrupted:
				print(f"\n⚠️ Alguns downloads podem estar incompletos!")

def main():
	# Args
	parse = argparse.ArgumentParser(description="Telegram Downloader - Baixa arquivos de Grupos ou Canais")

	parse.add_argument("-id", type=int, required=True, help="API ID do Telegram")
	parse.add_argument("-hash", type=str, required=True, help="API Hash do Telegram")
	parse.add_argument("-gc", type=str, help="ID do grupo ou canal para baixar arquivos")
	parse.add_argument("-lgc", action="store_true", help="Listar todos os chats, grupos ou canais")
	parse.add_argument("--p", type=str, help="Pasta personalizada para downloads")
	parse.add_argument("--ns", action="store_true", help="Deletar sessão após a execução")
	args = parse.parse_args()

	async def Td():
		async with TeleDownload(args.id, args.hash) as td:
			if args.lgc:
				await td.listChats()
			elif args.gc:
				await td.downloadFiles(args.gc, args.p)
			else:
				print(f"\nUso: teledownload.py [-h] or [--help]\n\nComandos\n\t-id\tAPI ID do Telegram\n\t-hash\tAPI Hash do Telegram\n\t-gc\tID do grupo ou canal para baixar arquivos\n\t-lgc\tListar todos os chats, grupos ou canais\n\t--p\tPasta personalizada para downloads\n\t--ns\tDeletar sessão após a execução\n\nExemplo\n\tpython teledownload.py -id 999 -hash 999 -lgc\n\tpython teledownload.py -id 999 -hash 999 -lgc --ns\n\tpython teledownload.py -id 999 -hash 999 -gc -100999\n\tpython teledownload.py -id 999 -hash 999 -gc -100999 --p \"./NomeDaPasta\"\n\tpython teledownload.py -id 999 -hash 999 -gc -100999 --ns\n")

	try:
		asyncio.run(Td())
	except KeyboardInterrupt:
		print("\n⚠️ [CTRL] + [C]")
	finally:
		if args.ns:
			sessionFile = 'session_teledownload.session'
			if os.path.exists(sessionFile):
				os.remove(sessionFile)
				print(f"\n✅ Sessão removida: {sessionFile}")

if __name__ == "__main__":
	main()