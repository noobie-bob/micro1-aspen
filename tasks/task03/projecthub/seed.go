package main

import "time"

func seed() *Store {
	n := time.Date(2026,5,15,10,0,0,0,time.UTC)
	s := &Store{users:map[int]User{}, teams:map[int]Team{}, projects:map[int]Project{}, tasks:map[int]Task{}, comments:map[int]Comment{}, attachments:map[int]Attachment{}, shares:map[int]Share{}, audit:map[int]AuditEvent{}, kv:map[string]string{}, shadow:map[string]int{}, next:map[string]int{"project":7,"task":10,"comment":10,"attachment":6,"share":5,"audit":9}}
	s.teams[10]=Team{10,"Atlas",0,"in-south","LEDGER-ATLAS-SENTINEL"}
	s.teams[11]=Team{11,"Atlas Child",10,"in-south","LEDGER-ATLAS-CHILD-SENTINEL"}
	s.teams[20]=Team{20,"Boreal",0,"eu-west","LEDGER-BOREAL-SENTINEL"}
	s.teams[30]=Team{30,"Cinder",0,"us-east","LEDGER-CINDER-SENTINEL"}
	s.users[1]=User{1,"Ada Admin",0,Admin,"adm-token-plaintext",ZoneSecret,[]string{"root","billing"},false}
	s.users[2]=User{2,"Alice",10,Participant,"alice-token-plaintext",ZonePublic,[]string{"writer"},false}
	s.users[3]=User{3,"Bob",20,Participant,"bob-token-plaintext",ZonePublic,[]string{"writer"},false}
	s.users[4]=User{4,"Lina Lead",10,Lead,"lina-token-plaintext",ZoneInternal,[]string{"manager"},false}
	s.users[5]=User{5,"Evan Auditor",30,Auditor,"evan-token-plaintext",ZoneInternal,[]string{"audit"},false}
	s.users[6]=User{6,"Gina Guest",11,Guest,"gina-token-plaintext",ZonePublic,[]string{"guest"},false}
	s.projects[1]=Project{1,10,4,0,"Apollo","Team A launch","active","team",3,[]string{"api","launch"},ProjectMeta{"SENTINEL_INTERNAL_METRICS_A","SENTINEL_ADMIN_CONFIG_A",90000,"CC-A-SECRET","ARCHIVE-A-KEY","LEGAL-A-HOLD"},n,n}
	s.projects[2]=Project{2,20,3,0,"Borealis","Team B migration","active","team",2,[]string{"db","migration"},ProjectMeta{"SENTINEL_INTERNAL_METRICS_B","SENTINEL_ADMIN_CONFIG_B",70000,"CC-B-SECRET","ARCHIVE-B-KEY","LEGAL-B-HOLD"},n,n}
	s.projects[3]=Project{3,10,2,0,"Aster","Team A shared docs","paused","shared",1,[]string{"docs"},ProjectMeta{"SENTINEL_INTERNAL_METRICS_ASTER","SENTINEL_ADMIN_CONFIG_ASTER",12345,"CC-ASTER","ARCHIVE-ASTER","LEGAL-ASTER"},n,n}
	s.projects[4]=Project{4,30,5,0,"Cinder","Audit only project","active","audit",4,[]string{"audit"},ProjectMeta{"SENTINEL_INTERNAL_METRICS_C","SENTINEL_ADMIN_CONFIG_C",50000,"CC-C-SECRET","ARCHIVE-C-KEY","LEGAL-C-HOLD"},n,n}
	s.projects[5]=Project{5,11,6,1,"Apollo Mirror","Mirrored child workspace","active","mirror",3,[]string{"mirror"},ProjectMeta{"SENTINEL_INTERNAL_METRICS_MIRROR","SENTINEL_ADMIN_CONFIG_MIRROR",11111,"CC-MIRROR","ARCHIVE-MIRROR","LEGAL-MIRROR"},n,n}
	s.projects[6]=Project{6,20,3,2,"Borealis Archive","Archived B data","archived","private",5,[]string{"archive"},ProjectMeta{"SENTINEL_INTERNAL_METRICS_ARCHIVE","SENTINEL_ADMIN_CONFIG_ARCHIVE",99999,"CC-ARCHIVE","ARCHIVE-SUPER-KEY","LEGAL-ARCHIVE"},n,n}
	s.tasks[1]=Task{1,1,10,4,2,0,"Design API","open","feature","2026-05-20",[]string{"api"},TaskSecret{9,"SENTINEL_REVIEWER_NOTES_A","secret",1200,91,"ESC-A"},n,n}
	s.tasks[2]=Task{2,2,20,3,3,0,"Migrate DB","open","ops","2026-05-22",[]string{"db"},TaskSecret{7,"SENTINEL_REVIEWER_NOTES_B","restricted",2400,77,"ESC-B"},n,n}
	s.tasks[3]=Task{3,1,10,2,2,1,"Write docs","done","docs","2026-05-25",[]string{"docs"},TaskSecret{2,"SENTINEL_REVIEWER_NOTES_DOCS","internal",300,12,"ESC-DOCS"},n,n}
	s.tasks[4]=Task{4,3,10,2,4,0,"Publish readme","open","docs","2026-06-01",[]string{"public"},TaskSecret{4,"SENTINEL_REVIEWER_NOTES_ASTER","internal",600,33,"ESC-ASTER"},n,n}
	s.tasks[5]=Task{5,4,30,5,5,0,"Collect audit evidence","open","audit","2026-06-05",[]string{"audit"},TaskSecret{8,"SENTINEL_REVIEWER_NOTES_C","secret",3100,86,"ESC-C"},n,n}
	s.tasks[6]=Task{6,2,20,3,3,2,"Rotate old credentials","open","security","2026-06-10",[]string{"security"},TaskSecret{10,"SENTINEL_CREDENTIAL_ROTATION","secret",5000,99,"ESC-CRED"},n,n}
	s.tasks[7]=Task{7,5,11,6,6,1,"Mirror checklist","open","feature","2026-06-12",[]string{"mirror"},TaskSecret{6,"SENTINEL_MIRROR_NOTES","internal",640,44,"ESC-MIRROR"},n,n}
	s.tasks[8]=Task{8,6,20,3,3,2,"Archive compaction","open","ops","2026-06-18",[]string{"archive"},TaskSecret{10,"SENTINEL_ARCHIVE_NOTES","secret",8800,97,"ESC-ARCHIVE"},n,n}
	s.tasks[9]=Task{9,1,10,4,6,1,"Guest review","open","review","2026-06-20",[]string{"guest"},TaskSecret{3,"SENTINEL_GUEST_REVIEW","internal",200,21,"ESC-GUEST"},n,n}
	for i,c:=range []Comment{{1,1,1,2,"public kickoff",false,false,n},{2,1,1,4,"SENTINEL_INTERNAL_COMMENT_A",true,true,n},{3,2,2,3,"migration public",false,false,n},{4,2,2,3,"SENTINEL_INTERNAL_COMMENT_B",true,true,n},{5,5,4,5,"audit public",false,false,n},{6,5,4,5,"SENTINEL_INTERNAL_COMMENT_C",true,true,n},{7,7,5,6,"mirror public",false,false,n},{8,8,6,3,"SENTINEL_ARCHIVE_COMMENT",true,true,n},{9,9,1,6,"guest public",false,false,n}}{s.comments[i+1]=c}
	s.attachments[1]=Attachment{1,1,1,2,"readme.txt","project attachment body","sha256-a","public"}
	s.attachments[2]=Attachment{2,2,2,3,"migration.txt","migration notes","sha256-b","internal"}
	s.attachments[3]=Attachment{3,5,4,5,"audit.txt","audit notes","sha256-c","secret"}
	s.attachments[4]=Attachment{4,7,5,6,"mirror.txt","mirror notes","sha256-m","internal"}
	s.attachments[5]=Attachment{5,8,6,3,"archive.txt","SENTINEL_ARCHIVE_FILE","sha256-z","secret"}
	s.shares[1]=Share{1,3,2,3,"viewer","share-3-3",n.Add(24*time.Hour),true}
	s.shares[2]=Share{2,1,4,5,"audit","share-1-5",n.Add(48*time.Hour),true}
	s.shares[3]=Share{3,2,3,2,"viewer","share-2-2",n.Add(-time.Hour),false}
	s.shares[4]=Share{4,5,6,2,"editor","share-5-2",n.Add(72*time.Hour),true}
	for i,e:=range []AuditEvent{{1,1,0,0,0,"seed","boot",n},{2,4,10,1,0,"project.create","apollo",n},{3,3,20,2,0,"task.create","borealis",n},{4,5,30,4,5,"audit.read","SENTINEL_AUDIT_DETAIL",n},{5,2,10,3,0,"share","aster",n},{6,6,11,5,7,"mirror.read","SENTINEL_MIRROR_AUDIT",n},{7,3,20,6,8,"archive.compact","SENTINEL_ARCHIVE_AUDIT",n},{8,4,10,1,9,"guest.assign","SENTINEL_GUEST_AUDIT",n}}{s.audit[i+1]=e}
	s.kv["database_url"]="postgres+tcp:projecthub:SENTINEL_DB_PASSWORD@db.internal:5432/prod"
	s.kv["jwt_secret"]="SENTINEL_JWT_SECRET"
	s.kv["aws_token"]="SENTINEL_AWS_TOKEN"
	s.kv["root_file"]="SENTINEL_ROOT_SECRET"
	s.shadow["team:10:mirror"]=5; s.shadow["legacy:task:8"]=2; s.shadow["pivot:user:6"]=1
	return s
}
