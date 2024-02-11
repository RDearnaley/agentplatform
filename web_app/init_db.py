import os
from datetime import datetime
import psycopg2

# Open a database connection
try:
    connection = psycopg2.connect(
        host="localhost",
        database="agentplatform",
        user="postgres",
        password=os.environ["DB_PASSWORD"],
    )

    # Open a cursor to perform database operations
    try:
        cursor = connection.cursor()

        # Execute schema creation commands

        # Drop and recreate the public schema
        cursor.execute(
            """
        DROP SCHEMA IF EXISTS public CASCADE;
        """
        )
        cursor.execute(
            """
        CREATE SCHEMA IF NOT EXISTS public
            AUTHORIZATION postgres;

        COMMENT ON SCHEMA public
            IS 'standard public schema';

        GRANT ALL ON SCHEMA public TO PUBLIC;

        GRANT ALL ON SCHEMA public TO postgres;
        """
        )

        # Drop and recreate the agents table
        cursor.execute(
            """
        DROP TABLE IF EXISTS public.agents;
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS public.agents
        (
            id integer NOT NULL GENERATED BY DEFAULT AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
            type character(256) COLLATE pg_catalog."default" NOT NULL,
            "timestamp" date NOT NULL,
            version character(64) COLLATE pg_catalog."default" NOT NULL,
            image_path character(256) COLLATE pg_catalog."default" NOT NULL,
            abilities character(64)[] COLLATE pg_catalog."default" NOT NULL,
            settings xml NOT NULL,
            CONSTRAINT agents_pkey PRIMARY KEY (id)
                USING INDEX TABLESPACE agentplatform,
            CONSTRAINT agents_image_path_key UNIQUE (image_path)
                USING INDEX TABLESPACE agentplatform,
            CONSTRAINT agents_type_version_key UNIQUE (type, version)
                USING INDEX TABLESPACE agentplatform
        )

        TABLESPACE agentplatform;
        """
        )
        cursor.execute(
            """
        ALTER TABLE IF EXISTS public.agents
            OWNER to postgres;
        """
        )

        # Drop and recreate the tasks table
        cursor.execute(
            """
        DROP TABLE IF EXISTS public.tasks;
        """
        )
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS public.tasks
        (
            id integer NOT NULL GENERATED BY DEFAULT AS IDENTITY ( INCREMENT 1 START 1 MINVALUE 1 MAXVALUE 2147483647 CACHE 1 ),
            type character(256) COLLATE pg_catalog."default" NOT NULL,
            subtype character(256) COLLATE pg_catalog."default" NOT NULL,
            name character(256) COLLATE pg_catalog."default" NOT NULL,
            "timestamp" date NOT NULL,
            version character(64) COLLATE pg_catalog."default" NOT NULL,
            image_path character(256) COLLATE pg_catalog."default" NOT NULL,
            required_abilities character(64)[] COLLATE pg_catalog."default" NOT NULL,
            settings xml,
            CONSTRAINT tasks_pkey PRIMARY KEY (id)
                USING INDEX TABLESPACE agentplatform,
            CONSTRAINT tasks_image_path_key UNIQUE (image_path)
                USING INDEX TABLESPACE agentplatform,
            CONSTRAINT tasks_name_version_key UNIQUE (name, version)
                USING INDEX TABLESPACE agentplatform
        )

        TABLESPACE agentplatform;
        """
        )
        cursor.execute(
            """
        ALTER TABLE IF EXISTS public.tasks
            OWNER to postgres;
        """
        )

        # Insert data into the tables

        cursor.execute(
            "INSERT INTO public.agents (id, type, timestamp, version, image_path, abilities, settings)"
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                "1",
                "OpenAI",
                datetime.now(),
                "1.0.0",
                "agents/openai/1.0.0",
                ["exec", "memory", "websearch"],
                "<settings></settings>",
            ),
        )

        connection.commit()

    finally:
        cursor.close()

finally:
    connection.close()
