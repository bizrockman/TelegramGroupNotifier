from datetime import datetime
from pyzotero.zotero import Zotero


class ZoteroHelper:

    def __init__(self, zotero_api_key, library_id, library_type='user'):
        self.zotero_client = Zotero(library_id, library_type, zotero_api_key)

    def get_latest_entries(self, limit=5):
        return self.zotero_client.top(limit=limit)

    def get_latest_entries_from_collection(self, collection_id, limit=5):
        return self.zotero_client.collection_items(collection_id, limit=limit)

    def get_latest_entries_from_collection_by_name(self, collection_name, limit=5):
        collection_id = self.find_collection_by_path(collection_name)
        if collection_id:
            return self.get_primary_items_from_collection(collection_id, limit=limit)
        else:
            return []

    def get_latest_created_after_by_collection_name(self, date_str, collection_name, limit=5, all_types=False):
        collection_id = self.find_collection_by_path(collection_name)
        if collection_id:
            return self.get_entries_created_after(date_str, collection_id, limit=limit, all_types=all_types)
        else:
            return []

    def get_all_collection_ids(self, collection_id):
        """
        Rekursive Funktion, um die IDs aller SubCollections einer Collection zu sammeln.
        """
        collection_ids = [collection_id]
        subcollections = self.zotero_client.collections_sub(collection_id)
        for subcollection in subcollections:
            subcollection_id = subcollection['key']
            collection_ids.extend(self.get_all_collection_ids(subcollection_id))
        return collection_ids

    def get_entries_created_after(self, date, collection_id, limit=5, all_types=False):
        date_filter = date.isoformat()
        all_collection_ids = self.get_all_collection_ids(collection_id)

        all_items = []
        for cid in all_collection_ids:
            params = {
                'limit': limit,
                'sort': 'dateAdded',
                'direction': 'desc',
            }

            if not all_types:
                params['itemType'] = '-attachment || note'

            items = self.zotero_client.collection_items(cid, **params)
            all_items.extend(items)

        sorted_items = sorted(all_items, key=lambda x: x['data']['dateAdded'], reverse=True)

        filtered_items = [item for item in sorted_items if item['data']['dateAdded'] > date_filter]

        if limit is not None:
            filtered_items = filtered_items[:limit]

        return filtered_items

    def get_primary_items_from_collection(self, collection_id, limit=5):
        params = {
            'itemType': '-attachment || note',
            # Dies ist ein Beispiel und funktioniert möglicherweise nicht wie erwartet
            'limit': limit
        }
        #items = self.zotero_client.collection_items(collection_id, limit=limit, content='json')
        items = self.zotero_client.collection_items(collection_id, **params)
        primary_items = items
        #primary_items = [item for item in items if item['itemType'] not in ['attachment', 'note']]
        return primary_items

    def find_collection_by_path(self, path, parent_collection_id=None):
        # Bestimmen, welche Sammlungen abgefragt werden sollen
        if parent_collection_id:
            collections = self.zotero_client.collections_sub(parent_collection_id)
        else:
            collections = self.zotero_client.collections_top() if '/' in path else self.zotero_client.all_collections()

        segments = path.split('/')
        for collection in collections:
            if collection['data']['name'] == segments[0]:
                # Letztes Segment erreicht, gewünschte Sammlung gefunden
                if len(segments) == 1:
                    return collection['data']['key']
                # Rekursion mit der nächsten Ebene des Pfades
                return self.find_collection_by_path('/'.join(segments[1:]), collection['data']['key'])

        # Warnung, wenn das Segment nicht gefunden wurde, und Rückgabe von None
        print(f"Warnung: Sammlung '{segments[0]}' nicht gefunden.")
        return None


def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()

    zoter_key = os.getenv('ZOTERO_API_KEY')
    zoter_user_id = os.getenv('ZOTERO_USER_ID')
    zotero_loader = ZoteroHelper(zoter_key, library_id=zoter_user_id)

    #entries = zotero_loader.get_latest_entries_from_collection_by_name('Papers/arxiv', limit=5)
    search_date = datetime.strptime('2024-02-15', '%Y-%m-%d')
    entries = zotero_loader.get_latest_created_after_by_collection_name(search_date, 'Papers/arxiv', limit=5)
    for entry in entries:
        print(entry['data']['title'])
        print(entry['data']['dateAdded'])


if __name__ == "__main__":
    main()
