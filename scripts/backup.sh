#!/bin/bash
set -e

echo "💾 Backup Banco de Dados VoxPop"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configurações
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="voxpop_prod"
DB_USER="voxpop"

# Criar diretório de backup
mkdir -p $BACKUP_DIR

echo -e "${YELLOW}📦 Criando backup do banco de dados...${NC}"

# Backup PostgreSQL do container
docker exec voxpop_postgres pg_dump -U $DB_USER -h localhost $DB_NAME > $BACKUP_DIR/voxpop_backup_$DATE.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup criado: voxpop_backup_$DATE.sql${NC}"
else
    echo -e "${RED}❌ Erro ao criar backup${NC}"
    exit 1
fi

# Backup dos arquivos de mídia
echo -e "${YELLOW}📁 Criando backup dos arquivos de mídia...${NC}"
docker run --rm -v voxpop_media:/data -v $(pwd)/backups:/backup alpine tar -czf /backup/voxpop_media_$DATE.tar.gz -C /data .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backup mídia: voxpop_media_$DATE.tar.gz${NC}"
else
    echo -e "${RED}❌ Erro ao criar backup de mídia${NC}"
    exit 1
fi

# Compactar backups antigos (manter apenas 7 dias)
echo -e "${YELLOW}🧹 Limpando backups antigos...${NC}"
find $BACKUP_DIR -name "voxpop_backup_*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "voxpop_media_*.tar.gz" -mtime +7 -delete

# Tamanho total do backup
BACKUP_SIZE=$(du -h $BACKUP_DIR/voxpop_backup_$DATE.sql | cut -f1)
MEDIA_SIZE=$(du -h $BACKUP_DIR/voxpop_media_$DATE.tar.gz | cut -f1)

echo -e "${GREEN}📊 Backup concluído!${NC}"
echo -e "${GREEN}📦 Banco: $BACKUP_SIZE${NC}"
echo -e "${GREEN}📁 Mídia: $MEDIA_SIZE${NC}"
echo -e "${YELLOW}💾 Localização: $BACKUP_DIR${NC}"

# Log do backup
echo "$(date): Backup realizado - DB: voxpop_backup_$DATE.sql ($BACKUP_SIZE), Media: voxpop_media_$DATE.tar.gz ($MEDIA_SIZE)" >> $BACKUP_DIR/backup.log