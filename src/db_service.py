from mysql.connector.pooling import PooledMySQLConnection

from src.spotify_service import TopItemsData


class DBService:
    def __init__(self, connection: PooledMySQLConnection):
        self.connection = connection

    def update_refresh_token(self, user_id: str, refresh_token: str):
        with self.connection.cursor() as cursor:
            update_statement = """
                UPDATE spotify_user
                SET refresh_token = (%s)
                WHERE user_id = (%s);
            """
            cursor.execute(update_statement, (user_id, refresh_token))
            self.connection.commit()

    def store_top_items(self, user_id: str, top_items_data: TopItemsData, collected_date: str):
        top_items = top_items_data.top_items
        item_type = top_items_data.item_type
        time_range = top_items_data.time_range

        insert_statement = f"""
            INSERT INTO top_{item_type} (spotify_user_id, {item_type}_id, collected_date, position, time_range)
            VALUES (%s, %s, %s, %s, %s);
        """

        values = [(user_id, item.id, collected_date, item.position, time_range) for item in top_items]

        with self.connection.cursor() as cursor:
            cursor.executemany(insert_statement, values)
            self.connection.commit()
