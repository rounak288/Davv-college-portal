document.addEventListener('DOMContentLoaded',()=>{
 const f=document.getElementById('imageInput'),p=document.getElementById('preview');
 if(f&&p)f.addEventListener('change',()=>{const file=f.files&&f.files[0];if(!file)return;const reader=new FileReader();reader.onload=e=>{p.innerHTML='';const img=document.createElement('img');img.src=e.target.result;img.alt='Event cover preview';p.appendChild(img)};reader.readAsDataURL(file)});
});
