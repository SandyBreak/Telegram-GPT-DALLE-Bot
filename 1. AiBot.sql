--SELECT QUERIES
select * from users;
select * from img_models;
select * from llm_models;
select * from model_roles;
select * from temporary_dialog_data;
select * from admin_group;


select tdd.id, tdd.id_tg, tdd.role_id, lm.name as llm_model, im."name" as img_model, tdd.quality_generated_image from ai_bot.temporary_dialog_data tdd
JOIN llm_models lm ON tdd.llm_model_id=lm.id
JOIN img_models im ON tdd.img_model_id=im.id;

select tdd.id, tdd.id_tg, mr.name_role, mr.history_dialog as history_dialog, lm.value as llm_model, im.value as img_model, tdd.quality_generated_image from temporary_dialog_data tdd
JOIN llm_models lm ON tdd.llm_model_id=lm.id
JOIN img_models im ON tdd.img_model_id=im.id
JOIN model_roles mr ON tdd.role_id=mr.id; 
--where tdd.id_tg = 5890864355;
SELECT * FROM pg_stat_activity;
