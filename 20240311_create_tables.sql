-- Включаем расширение для работы с UUID
create extension if not exists "uuid-ossp";

-- Включаем расширение для работы с векторами
create extension if not exists vector;

-- Создаем таблицу для файлов
create table if not exists source_files (
    id uuid primary key default uuid_generate_v4(),
    file_path text not null unique,
    file_name text not null,
    summary text,
    metadata jsonb,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    updated_at timestamp with time zone default timezone('utc'::text, now())
);

-- Создаем индекс для поиска по имени файла
create index if not exists idx_source_files_file_name on source_files (file_name);

-- Создаем таблицу для векторных представлений summary файлов
create table if not exists file_summary_embeddings (
    id uuid primary key default uuid_generate_v4(),
    file_id uuid references source_files(id) on delete cascade,
    embedding vector(384),
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Создаем индекс для векторного поиска по summary
create index if not exists idx_file_summary_embeddings_embedding on file_summary_embeddings 
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Создаем таблицу для параграфов
create table if not exists paragraphs (
    id uuid primary key default uuid_generate_v4(),
    file_id uuid references source_files(id) on delete cascade,
    text text not null,
    paragraph_type text,
    metadata jsonb,
    position_in_file integer,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Создаем индекс для поиска по тексту
create index if not exists idx_paragraphs_text on paragraphs using gin (to_tsvector('english', text));
create index if not exists idx_paragraphs_file_id on paragraphs (file_id);
create index if not exists idx_paragraphs_position on paragraphs (file_id, position_in_file);

-- Создаем таблицу для векторных представлений параграфов
create table if not exists paragraph_embeddings (
    id uuid primary key default uuid_generate_v4(),
    paragraph_id uuid references paragraphs(id) on delete cascade,
    embedding vector(384),
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Создаем индекс для векторного поиска по параграфам
create index if not exists idx_paragraph_embeddings_embedding on paragraph_embeddings 
using ivfflat (embedding vector_cosine_ops)
with (lists = 100);

-- Создаем индекс для связи с параграфами
create index if not exists idx_paragraph_embeddings_paragraph_id on paragraph_embeddings (paragraph_id);

-- Добавляем комментарии к таблицам
comment on table source_files is 'Table for storing information about source files';
comment on table file_summary_embeddings is 'Table for storing vector representations of file summaries';
comment on table paragraphs is 'Table for storing text paragraphs from documents';
comment on table paragraph_embeddings is 'Table for storing vector representations of paragraphs';

-- Добавляем комментарии к колонкам source_files
comment on column source_files.file_path is 'Full path to the file';
comment on column source_files.file_name is 'File name';
comment on column source_files.summary is 'Summary of the file';
comment on column source_files.metadata is 'Additional metadata about the file in JSON format';

-- Добавляем комментарии к колонкам paragraphs
comment on column paragraphs.file_id is 'Link to the source file';
comment on column paragraphs.text is 'Text of the paragraph';
comment on column paragraphs.paragraph_type is 'Type of the paragraph (e.g. text, header, list)';
comment on column paragraphs.metadata is 'Additional metadata about the paragraph in JSON format';
comment on column paragraphs.position_in_file is 'Position of the paragraph in the file';

-- Добавляем комментарии к колонкам embeddings
comment on column paragraph_embeddings.paragraph_id is 'Link to the paragraph';
comment on column paragraph_embeddings.embedding is 'Vector representation of the paragraph text';
comment on column file_summary_embeddings.file_id is 'Link to the file';
comment on column file_summary_embeddings.embedding is 'Vector representation of the file summary';

-- Создаем функцию для поиска похожих параграфов
create or replace function match_paragraphs(
    query_embedding vector(384),
    match_threshold float default 0.7,
    match_count int default 5
)
returns table (
    id uuid,
    text text,
    file_path text,
    file_name text,
    paragraph_type text,
    metadata jsonb,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        p.id,
        p.text,
        sf.file_path,
        sf.file_name,
        p.paragraph_type,
        p.metadata,
        1 - (pe.embedding <=> query_embedding) as similarity
    from paragraphs p
    join paragraph_embeddings pe on p.id = pe.paragraph_id
    join source_files sf on p.file_id = sf.id
    where 1 - (pe.embedding <=> query_embedding) > match_threshold
    order by similarity desc
    limit match_count;
end;
$$;

-- Создаем функцию для поиска похожих файлов по summary
create or replace function match_files_by_summary(
    query_embedding vector(384),
    match_threshold float default 0.7,
    match_count int default 5
)
returns table (
    id uuid,
    file_path text,
    file_name text,
    summary text,
    metadata jsonb,
    similarity float
)
language plpgsql
as $$
begin
    return query
    select
        sf.id,
        sf.file_path,
        sf.file_name,
        sf.summary,
        sf.metadata,
        1 - (fse.embedding <=> query_embedding) as similarity
    from source_files sf
    join file_summary_embeddings fse on sf.id = fse.file_id
    where 1 - (fse.embedding <=> query_embedding) > match_threshold
    order by similarity desc
    limit match_count;
end;
$$; 