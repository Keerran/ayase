CREATE OR REPLACE FUNCTION array_reverse(anyarray) RETURNS anyarray AS $$
SELECT ARRAY(
    SELECT $1[i]
    FROM generate_subscripts($1,1) AS s(i)
    ORDER BY i DESC
);
$$ LANGUAGE 'sql' STRICT IMMUTABLE;


CREATE OR REPLACE FUNCTION reverse_name(text) RETURNS text AS $$
    SELECT array_to_string(array_reverse(string_to_array($1, ' ')), ' ');
$$ LANGUAGE 'sql' STRICT IMMUTABLE;
-- UPDATE characters
--     SET name = array_to_string(array_reverse(string_to_array(name, ' ')), ' ')
--     FROM medias
--     WHERE characters.media_id = medias.id
--     AND medias.title = 'One Piece';
