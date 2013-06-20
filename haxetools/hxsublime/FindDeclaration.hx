package hxsublime;


#if macro
using haxe.macro.ExprTools;
using haxe.macro.TypeTools;

import haxe.ds.Option;
import haxe.macro.Context;
import haxe.macro.Expr;
import haxe.macro.Expr.ExprOf;
import haxe.macro.Type;
import haxe.macro.TypeTools;
import neko.Lib;
using StringTools;

typedef FieldInfosData = {
	var pos(default,null):haxe.macro.Position;
	var doc(default, null):Null<String>;
}

typedef FieldInfos = Option<FieldInfosData>; 
#end



class FindDeclaration 
{


	#if macro

	static function outResult (info:FieldInfos, success:FieldInfosData->String = null, error = null) {
		if (error == null) {
			error = function () return "";
		}
		if (success == null) {
			success = function (f) return formatPos(f.pos);
		}


		switch (info) {
			case Some(f): 
				out(Std.string(f));
				out(success(f));
			case None: out(error());
		}

	}
	static function formatPos (pos:Position) 
	{
		var p = Context.getPosInfos( pos );
		var file = p.file.split("\\").join("/");
		return '|||||{ "file": "$file", "min" : ${p.min}, "max" : ${p.max} }|||||';
	}

	static function formatDoc (doc:Null<String>) 
	{
		var doc = doc == null ? "" : doc;
		return '|||||{ "doc": "$doc" }|||||';
	}

	static function redirectTrace () 
	{
		
		haxe.Log.trace = function (msg, ?pos:haxe.PosInfos) 
		{
			var f = pos.fileName;
			var p = f.substr(f.lastIndexOf("/")+1) + ":" + pos.lineNumber;
			out(p + ": " + msg);
		}
	}

	static function error (info:String = "impossible") 
	{
		return '|||||{ "error": "${info}" }|||||';
	}

	static function fromIdent (x):FieldInfos 
	{
		return try {
			var t = Context.typeof( x );

			var info:FieldInfos = switch (t) {
				case Type.TAbstract( t , _ ): Some(t.get());
				case Type.TEnum( t , _ ):     Some(t.get());
				case Type.TInst( t , _ ):     Some(t.get());
				case Type.TType( t , _ ):     Some(t.get());
				case _: None;
			}
			info;

		} catch (e:Dynamic) {
			None;
		}
	}

	static function findInInstance (t:Ref<ClassType>, check):FieldInfos
	{
		var cur = t;

		var res:FieldInfos = None;
		var interf1 = [];

		trace(t.get());
		trace(t.get().meta.get());
		while (res == None) {

			var fields = cur.get().fields.get().filter( check );
			
			if (fields.length == 1)  {
				var x:FieldInfosData = fields[0];
				res = Some(x);
			} 
			else 
			{
				var x = cur.get().superClass;
				if (x == null) break;

				cur = x.t;

				for (i in cur.get().interfaces) {

					interf1.push(i);
				}
			}
		}
		if (res == None) {
			var interf = t.get().interfaces.concat(interf1);
			while (res == None && interf.length > 0) {
				var new_interf = [];
				for (i in interf) {
					var fields = i.t.get().fields.get().filter( check );
					if (fields.length == 1)  {
						res = Some(fields[0]);
						
					} else {
						for (i in i.t.get().interfaces) {
							new_interf.push(i);
						}
					}
				}
				if (res == None) {
					interf = new_interf;	
				}
				
			}
		}

		return res;
	}

	static function fromField (x, field:String):FieldInfos
	{
		out(field);
		function check (x:ClassField) 
		{
			return if (field.startsWith("get_") || field.startsWith("set_")) 
			{
				x.name == field.substr(4);
			} else {
				x.name == field;
			}
		}

		var info:FieldInfos = try {
			trace("Trying to get the type of expression x");
			trace("this could fail/stop without a thrown exception (Haxe Compiler Bug in Display mode)");
			var t = Context.typeof( x );
			trace("x was successfull typed as: << " + TypeTools.toString(t) + " >>");
			switch (t) 
			{
				case Type.TInst( t , _ ):
					trace("Search in TInst");
					findInInstance(t, check);

					
				case Type.TType( t , _ ):
					trace("Search in TType");
					switch (t.get().type) {
						case Type.TInst( t , _ ):
							var statics = t.get().statics.get().filter( check );
							//var fields = t.get().fields.get().filter( check );

							trace(t.get());

							Some(statics[0]);
							
							

						case Type.TAnonymous( a ):
							var fields = a.get().fields.filter(check);
							Some(fields[0]);

						case _: 
							trace("unsupported");
							None;


					}
				case Type.TAnonymous( a ):
					trace("Search in TAnonymous");
					var fields = a.get().fields.filter(check);
					Some(fields[0]);
				case _:

					trace("Declaration is not available");
					None;
			}

			// jump to field
			// consider using
			
		}  catch (e:Dynamic) {
			
			// jump to type
			trace("hey5");
			trace("no type");

			var x2 = macro $x.$field;

			fromIdent(x2);

			
		}
		out("hey5");
		return info;

	}

	static var out = Lib.println;

	static function checkRegular (e):FieldInfos 
	{
		
		return switch (e.expr) 
		{
			case EConst(CIdent(_)):
				trace("Current Expression is an const Ident");
				var p = fromIdent(e);
				p;
			case EField(e, field):
				trace("Current Expression is a field access (EField)");
				var p = fromField(e,field);

				if (p == null) 
					out(error());
				p;
				

			// compiler inlined expression
			case ECall({expr:EFunction(_,
				{ expr : { expr : 
					EReturn( 
						{ expr : EFunction(_, { expr : { expr : EReturn(
							x
						)}})}
					)
				}})}, _):
				trace("Current Expression is a compiler inlined Expression (hard to follow)");
				switch (x) 
				{
					case {expr:ECall({ expr : EField(e, field)}, _)}:
						trace("Inlined Expression contains Field Access, try fromField");
						var p = fromField(e,field);
						if (p == null) 
							out(error());
						p;

					case _:
						trace("Inlined Expression cannot be resolved");
						
						trace("Trigger inline error for sublime, the inline workaround can be triggered from there.");
						out(error("inlined"));
						None;
						
						
				}
			case ECall({expr : EField(e,field)}, args) if (args.length == 0):
				trace("Expression is an ECall from an EField, try fromField");
				var p = fromField(e,field);
				if (p == null) 
					out(error());
				p;

			case _:
				out(error());
				None;
		}
	}

	static function sublimeFindDecl (e:Expr, eIdent:Expr, formatField:FieldInfosData->String) 
	{
		redirectTrace();

		trace("-------------------");
		trace("Find Declaration of Expr: " + e.toString());



		// this is a special check, eIdent is only passed to this function
		// if a first regular call was not successfull. This could be
		// the case if the expression was inlined by the compiler
		// and couldn't be checked afterwards.
		var info = switch (eIdent.expr) 
		{
			case EConst(CIdent(fieldName)) if (fieldName != "null"):
				trace("Using Inline Workaround for id " + fieldName);
				var p = fromField(e, fieldName);
				if (p != None) 
				{
					p;
				}
				else 
				{
					out(error());
					None;
				};
			case _:
				None;
		}

		if (info == None) {
			// if e is a type
			info = switch (Context.typeof(e)) 
			{
				case TType(t, params):
					trace("Expr is a TType");
					Some(t.get());
					
				case t:
					trace("Type of Expr is << " + TypeTools.toString(t) + " >>");
					None;
			}
		}

		if (info == None) {

			// find decl based on the structure of expression e
			info = checkRegular(e);

			
		}
		if (info != None) {
			outResult(info, formatField);
		}
		out("-------------------");
		return macro null;
	}


	#end



	macro public static function __sublimeFindDecl (e:ExprOf<Dynamic>, eIdent:Expr = null):Expr 
	{
		return sublimeFindDecl(e, eIdent, function (f) return formatPos(f.pos));
	}
	macro public static function __sublimePrintDoc (e:ExprOf<Dynamic>, eIdent:Expr = null):Expr 
	{
		return sublimeFindDecl(e, eIdent, function (f) return formatDoc(f.doc));
	}

}