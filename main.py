import logging
from src.utils.get_data import get_caract_2023, get_radar_2023
from src.utils.clean_caract_2023 import clean_caract
from src.utils.clean_radars_2023 import clean_radars
from src.utils.merge_data import merge_cleaned_year


# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    try:
        # 1. Téléchargement des données brutes
        logger.info("Début du téléchargement des données...")
        get_caract_2023()
        get_radar_2023()
        logger.info("Téléchargement terminé.")


        # 2. Nettoyage des données
        logger.info("Début du nettoyage des données...")
       
        # Nettoyage des caractéristiques d'accidents
        logger.info("Nettoyage des données d'accidents...")
        df_caract_clean = clean_caract()
        logger.info(f"Données d'accidents nettoyées: {len(df_caract_clean)} entrées")


        # Nettoyage des données radar
        logger.info("Nettoyage des données radar...")
        df_radars_clean = clean_radars()
        logger.info(f"Données radar nettoyées: {len(df_radars_clean)} entrées")


        logger.info("Processus de traitement des données terminé : nettoyage ok.")


        # 3. Fusion des fichiers nettoyés
        logger.info("Fusion des fichiers nettoyés (tous) ...")
        try:
            merged = merge_cleaned_year(None, primary_key='acc_id')
            logger.info(f"Fichier fusionné généré : {merged}")
        except Exception as me:
            logger.warning(f"La fusion des fichiers nettoyés a échoué : {me}")


    except Exception as e:
        logger.error(f"Une erreur est survenue: {str(e)}")
        raise


if __name__ == "__main__":
    main()
