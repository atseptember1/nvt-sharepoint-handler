CREATE TABLE Files(  
    id int NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary Key',
    UploadDate DATETIME COMMENT 'Create Time',
    FileName NVARCHAR(255),
    FileUrl NVARCHAR(255),
    Size FLOAT

) COMMENT '';